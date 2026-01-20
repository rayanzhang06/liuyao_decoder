"""六爻解读多Agent系统 - 主入口"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from loguru import logger

from config.config_loader import Config
from utils.parser import HexagramParser
from agents.orchestrator import DebateOrchestrator
from utils.report_generator import ReportGenerator
from storage.models import HexagramInput
from storage.database import DatabaseManager


console = Console()


class LiuyaoDecoderApp:
    """主应用类 - 协调整个解码流程"""

    def __init__(self, config_path: Optional[str] = None, require_agents: bool = False):
        """
        初始化应用

        Args:
            config_path: 可选的配置文件路径
            require_agents: 是否需要初始化 Agent（用于 list/view/delete 等不需要 Agent 的命令）
        """
        try:
            self.config = Config(config_path)
            self.parser = HexagramParser()
            self.report_generator = ReportGenerator()
            self.database = DatabaseManager(self.config)

            # 延迟初始化 Orchestrator
            self._orchestrator = None
            if require_agents:
                self._get_orchestrator()

            logger.info("应用初始化成功")
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            console.print(f"[bold red]应用初始化失败: {e}[/bold red]")
            raise

    def _get_orchestrator(self) -> DebateOrchestrator:
        """获取或创建 DebateOrchestrator（延迟初始化）"""
        if self._orchestrator is None:
            self._orchestrator = DebateOrchestrator(self.config)
        return self._orchestrator

    @property
    def orchestrator(self) -> DebateOrchestrator:
        """获取 orchestrator（属性访问）"""
        return self._get_orchestrator()

    async def process_hexagram_text(self,
                                    text: str,
                                    save_to_db: bool = False,
                                    output_file: Optional[str] = None) -> str:
        """
        处理卦象文本

        Args:
            text: 卦象文本（遵循prompt_v2.md格式）
            save_to_db: 是否保存到数据库（Stage 2实现）
            output_file: 可选的输出报告文件路径

        Returns:
            str: 生成的markdown报告
        """
        try:
            # Stage 1: 解析卦象
            with console.status("[bold yellow]解析卦象..."):
                hexagram = self.parser.parse_text(text)
                console.print(f"✅ 卦象解析成功: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")

            # Stage 2: 运行辩论
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[bold yellow]进行多流派辩论...", total=None)

                context = await self.orchestrator.run_debate(hexagram)

                progress.update(task, completed=True)
                console.print(f"✅ 辩论完成: 第 {context.current_round} 轮")
                console.print(f"   收敛分数: {context.convergence_score:.2f}")
                console.print(f"   辩论状态: {context.state.value}")

            # Stage 3: 生成报告
            with console.status("[bold yellow]生成报告..."):
                report = self.report_generator.generate_report(context)
                console.print("✅ 报告生成成功")

            # Stage 4: 保存到文件（如果指定）
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(report, encoding='utf-8')
                console.print(f"✅ 报告已保存: {output_path}")

            # Stage 5: 保存到数据库（如果启用）
            if save_to_db:
                record = self.database.save_debate(context, report)
                console.print(f"✅ 已保存到数据库 (ID: {record.id})")

            return report

        except Exception as e:
            logger.exception("处理卦象失败")
            console.print(f"❌ 处理失败: {e}", style="bold red")
            raise


# ==================== CLI 命令 ====================

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """六爻解读多Agent系统 - 命令行接口

    基于prompt_v2.md设计文档实现的多流派辩论系统
    """
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', help='输出报告文件路径 (markdown格式)')
@click.option('--no-save', is_flag=True, help='不保存到数据库')
@click.option('--config', '-c', help='配置文件路径')
def decode(input_file: str, output: Optional[str], no_save: bool, config: Optional[str]):
    """解读卦象文件

    示例:
        python main.py decode hexagram.txt -o report.md
        python main.py decode hexagram.txt --no-save
    """
    try:
        # 读取输入文件
        text = Path(input_file).read_text(encoding='utf-8')

        # 运行应用
        app = LiuyaoDecoderApp(config, require_agents=True)
        report = asyncio.run(app.process_hexagram_text(
            text=text,
            save_to_db=not no_save,
            output_file=output
        ))

        # 如果没有指定输出文件，打印到控制台
        if not output:
            console.print("\n" + "="*80 + "\n")
            console.print(report)
            console.print("\n" + "="*80 + "\n")

        return 0

    except Exception as e:
        console.print(f"❌ 解读失败: {e}", style="bold red")
        logger.exception("decode命令失败")
        return 1


@cli.command()
@click.argument('hexagram_text', type=str)
@click.option('--output', '-o', help='输出报告文件路径')
@click.option('--no-save', is_flag=True, help='不保存到数据库')
@click.option('--config', '-c', help='配置文件路径')
def decode_text(hexagram_text: str, output: Optional[str], no_save: bool, config: Optional[str]):
    """直接解读卦象文本

    示例:
        python main.py decode-text "-----
    灵光象吉·六爻排盘
    时间：2025年11月18日 23:57:20
    ..."
    """
    try:
        app = LiuyaoDecoderApp(config, require_agents=True)
        report = asyncio.run(app.process_hexagram_text(
            text=hexagram_text,
            save_to_db=not no_save,
            output_file=output
        ))

        if not output:
            console.print("\n" + "="*80 + "\n")
            console.print(report)
            console.print("\n" + "="*80 + "\n")

        return 0

    except Exception as e:
        console.print(f"❌ 解读失败: {e}", style="bold red")
        logger.exception("decode-text命令失败")
        return 1


@cli.command()
@click.option('--limit', '-l', default=20, help='显示数量')
@click.option('--offset', '-o', default=0, help='偏移量')
@click.option('--config', '-c', help='配置文件路径')
def list(limit: int, offset: int, config: Optional[str]):
    """列出历史辩论记录

    示例:
        python main.py list -l 10
        python main.py list --limit 5 --offset 10
    """
    try:
        app = LiuyaoDecoderApp(config)
        records = app.database.list_debates(limit=limit, offset=offset)

        if not records:
            console.print("📭 暂无辩论记录")
            return 0

        table = Table(title=f"辩论记录 (共 {len(records)} 条)")
        table.add_column("ID", style="cyan")
        table.add_column("时间", style="green")
        table.add_column("卦象", style="yellow")
        table.add_column("收敛轮次", style="magenta")
        table.add_column("收敛分数", style="blue")

        for record in records:
            # 从JSON中提取卦象名称
            hex_data = json.loads(record.hexagram_input)
            ben_gua = hex_data.get('ben_gua_name', '未知')
            bian_gua = hex_data.get('bian_gua_name', '未知')
            gua_str = f"{ben_gua} → {bian_gua}"

            table.add_row(
                str(record.id),
                record.timestamp.strftime('%Y-%m-%d %H:%M'),
                gua_str,
                str(record.convergence_round) or "未收敛",
                f"{record.convergence_score:.2f}"
            )

        console.print(table)
        return 0

    except Exception as e:
        console.print(f"❌ 查询失败: {e}", style="bold red")
        logger.exception("list命令失败")
        return 1


@cli.command()
@click.argument('debate_id', type=int)
@click.option('--output', '-o', help='输出报告文件路径')
@click.option('--config', '-c', help='配置文件路径')
def view(debate_id: int, output: Optional[str], config: Optional[str]):
    """查看历史辩论记录

    示例:
        python main.py view 123 -o report.md
        python main.py view 123
    """
    try:
        app = LiuyaoDecoderApp(config)
        record = app.database.load_debate(debate_id)

        if not record:
            console.print(f"❌ 未找到辩论记录: {debate_id}", style="bold red")
            return 1

        report = record.final_report or "(报告未生成)"

        if output:
            Path(output).write_text(report, encoding='utf-8')
            console.print(f"✅ 报告已保存: {output}")
        else:
            console.print("\n" + "="*80 + "\n")
            console.print(report)
            console.print("\n" + "="*80 + "\n")

        return 0

    except Exception as e:
        console.print(f"❌ 查看失败: {e}", style="bold red")
        logger.exception("view命令失败")
        return 1


@cli.command()
@click.argument('debate_id', type=int)
@click.option('--config', '-c', help='配置文件路径')
@click.confirmation_option(prompt='确认删除此辩论记录？')
def delete(debate_id: int, config: Optional[str]):
    """删除历史辩论记录

    示例:
        python main.py delete 123
    """
    try:
        app = LiuyaoDecoderApp(config)
        success = app.database.delete_debate(debate_id)

        if success:
            console.print(f"✅ 已删除辩论记录: {debate_id}")
            return 0
        else:
            console.print(f"❌ 未找到辩论记录: {debate_id}", style="bold red")
            return 1

    except Exception as e:
        console.print(f"❌ 删除失败: {e}", style="bold red")
        logger.exception("delete命令失败")
        return 1


@cli.command()
def test_config():
    """测试配置是否正确

    示例:
        python main.py test-config
    """
    try:
        console.print("🔍 测试配置文件...\n")

        config = Config()

        # 测试LLM配置
        console.print("✅ LLM配置:")
        for client_name in ['kimi', 'glm', 'deepseek', 'openai', 'anthropic', 'gemini']:
            client_config = config.get_llm_config(client_name)
            api_key = client_config.get('api_key', '')
            status = "✅" if api_key else "❌"
            console.print(f"   {status} {client_name}: {client_config['model']}")
            if not api_key:
                console.print(f"      [yellow]未配置API密钥[/yellow]")

        # 测试Agent配置
        console.print("\n✅ Agent配置:")
        for agent_name in ['traditional', 'xiangshu', 'mangpai']:
            agent_config = config.get_agent_config(agent_name)
            console.print(f"   {agent_config['school']}: {agent_config['llm_client']} ({agent_config['model']})")

        # 测试辩论配置
        console.print("\n✅ 辩论配置:")
        debate_config = config.get_debate_config()
        console.print(f"   最大轮数: {debate_config['max_rounds']}")
        console.print(f"   收敛阈值: {debate_config['convergence_threshold']}")

        console.print("\n[bold green]✅ 配置测试完成[/bold green]")
        return 0

    except Exception as e:
        console.print(f"❌ 配置测试失败: {e}", style="bold red")
        logger.exception("test-config命令失败")
        return 1


@cli.command()
def interactive():
    """进入交互式界面

    示例:
        python main.py interactive
    """
    # 清屏
    console.clear()

    # 显示欢迎界面
    welcome_text = Text()
    welcome_text.append("六爻解读多Agent系统", style="bold cyan")
    welcome_text.append("\n", style="")
    welcome_text.append("基于多流派辩论的智能卦象解读", style="dim")
    welcome_text.append("\n" + "="*50 + "\n", style="dim")

    console.print(Panel(welcome_text, border_style="cyan"))

    app = None

    while True:
        console.print("\n")
        menu_table = Table(title="主菜单", show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("选项", style="cyan")
        menu_table.add_column("说明", style="dim")

        menu_table.add_row("1. 解读卦象", "从文件或直接输入解读卦象")
        menu_table.add_row("2. 查看历史", "列出和查看历史辩论记录")
        menu_table.add_row("3. 删除记录", "删除指定的辩论记录")
        menu_table.add_row("4. 测试配置", "测试 API 配置是否正确")
        menu_table.add_row("0. 退出", "退出程序")

        console.print(menu_table)

        choice = Prompt.ask(
            "\n请选择操作",
            choices=["0", "1", "2", "3", "4"],
            default="1"
        )

        if choice == "0":
            console.print("\n[bold green]感谢使用，再见！[/bold green]")
            break

        elif choice == "1":
            _interactive_decode(console, app)

        elif choice == "2":
            if app is None:
                app = LiuyaoDecoderApp()
            _interactive_list(console, app)

        elif choice == "3":
            if app is None:
                app = LiuyaoDecoderApp()
            _interactive_delete(console, app)

        elif choice == "4":
            _interactive_test_config(console)


def _interactive_decode(console: Console, app):
    """交互式解读卦象"""
    console.print("\n[bold cyan]解读卦象[/bold cyan]")

    # 选择输入方式
    input_method = Prompt.ask(
        "\n请选择输入方式",
        choices=["file", "text", "back"],
        default="file"
    )

    if input_method == "back":
        return

    try:
        if app is None:
            app = LiuyaoDecoderApp(require_agents=True)
        else:
            # 确保已初始化 Agent
            if app._orchestrator is None:
                app._get_orchestrator()

        hexagram_text = ""
        if input_method == "file":
            file_path = Prompt.ask("\n请输入卦象文件路径")
            path = Path(file_path)
            if not path.exists():
                console.print(f"[bold red]文件不存在: {file_path}[/bold red]")
                return
            hexagram_text = path.read_text(encoding='utf-8')
            console.print(f"[green]✅ 已读取文件[/green]")

        else:  # text
            console.print("\n[yellow]请输入卦象文本:[/yellow]")
            console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]")
            console.print("[dim]提示:[/dim]")
            console.print("[dim]  1. 粘贴卦象文本（支持多行）[/dim]")
            console.print("[dim]  2. 输入完成后，在新行输入 === 并按回车[/dim]")
            console.print("[dim]  3. 或直接输入文件路径[/dim]")
            console.print("[dim]  4. 或输入 'back' 返回上一步[/dim]")
            console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/cyan]\n")

            lines = []
            line_count = 0
            hexagram_loaded = False  # 标记是否已加载卦象文本
            while True:
                try:
                    prompt_text = f"[{line_count}]> " if line_count == 0 else "... "
                    line = Prompt.ask(prompt_text, show_default=False)
                    line_stripped = line.strip()

                    # 检查结束标记
                    if line_stripped == "===":
                        if lines:
                            break
                        else:
                            console.print("[yellow]请先输入内容[/yellow]")
                            continue

                    # 检查返回命令
                    if line_stripped.lower() == "back" and not lines:
                        return

                    # 检查是否是文件路径（仅当还没有输入内容时）
                    if not lines and Path(line_stripped).exists():
                        hexagram_text = Path(line_stripped).read_text(encoding='utf-8')
                        hexagram_loaded = True
                        console.print(f"[green]✅ 已从文件读取: {line_stripped}[/green]")
                        break

                    lines.append(line)
                    line_count += 1

                except EOFError:
                    # 用户按 Ctrl-D
                    if lines:
                        break
                    else:
                        console.print("[yellow]已取消输入[/yellow]")
                        return

            if not lines and not hexagram_loaded:
                console.print("[yellow]未输入任何内容[/yellow]")
                return

            if not hexagram_loaded:
                hexagram_text = "\n".join(lines)
                console.print(f"[green]✅ 已读取 {len(lines)} 行文本[/green]")

        # 询问是否保存到数据库
        save_to_db = Confirm.ask("\n是否保存到数据库", default=True)

        # 询问输出文件
        output_file = Prompt.ask("\n输出报告文件路径（可选，按回车跳过）", default="")

        # 运行解读
        console.print("\n")
        report = asyncio.run(app.process_hexagram_text(
            text=hexagram_text,
            save_to_db=save_to_db,
            output_file=output_file if output_file else None
        ))

        # 如果没有输出文件，询问是否显示报告
        if not output_file:
            show_report = Confirm.ask("\n是否显示完整报告", default=False)
            if show_report:
                console.print("\n" + "="*80 + "\n")
                console.print(report)
                console.print("\n" + "="*80 + "\n")

    except Exception as e:
        console.print(f"\n[bold red]❌ 解读失败: {e}[/bold red]")
        logger.exception("交互式解读失败")

    # 等待用户确认
    console.print("\n[dim]按回车返回主菜单...[/dim]")
    input()


def _interactive_list(console: Console, app: LiuyaoDecoderApp):
    """交互式查看历史"""
    console.print("\n[bold cyan]查看历史记录[/bold cyan]")

    try:
        # 显示记录列表
        records = app.database.list_debates(limit=20)

        if not records:
            console.print("\n[yellow]📭 暂无辩论记录[/yellow]")
            console.print("\n[dim]按回车返回主菜单...[/dim]")
            input()
            return

        # 显示记录列表
        table = Table(title=f"辩论记录 (共 {len(records)} 条)")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("时间", style="green", width=18)
        table.add_column("卦象", style="yellow", width=25)
        table.add_column("轮次", style="magenta", width=6)
        table.add_column("收敛", style="blue", width=8)

        for record in records:
            hex_data = json.loads(record.hexagram_input)
            ben_gua = hex_data.get('ben_gua_name', '未知')
            bian_gua = hex_data.get('bian_gua_name', '未知')
            gua_str = f"{ben_gua} → {bian_gua}"
            if len(gua_str) > 23:
                gua_str = gua_str[:20] + "..."

            table.add_row(
                str(record.id),
                record.timestamp.strftime('%Y-%m-%d %H:%M'),
                gua_str,
                str(record.convergence_round) or "未收敛",
                f"{record.convergence_score:.2f}"
            )

        console.print("\n")
        console.print(table)

        # 询问是否查看某条记录
        action = Prompt.ask(
            "\n请选择操作",
            choices=["view", "back"],
            default="back"
        )

        if action == "view":
            record_id = Prompt.ask("\n请输入要查看的记录ID", type=int)
            record = app.database.load_debate(record_id)

            if record:
                report = record.final_report or "(报告未生成)"
                console.print("\n" + "="*80 + "\n")
                console.print(report)
                console.print("\n" + "="*80 + "\n")

                # 询问是否导出
                export = Confirm.ask("\n是否导出到文件", default=False)
                if export:
                    output_path = Prompt.ask("请输入输出文件路径", default=f"report_{record_id}.md")
                    Path(output_path).write_text(report, encoding='utf-8')
                    console.print(f"[green]✅ 已导出到: {output_path}[/green]")
            else:
                console.print(f"[bold red]❌ 未找到记录: {record_id}[/bold red]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 查询失败: {e}[/bold red]")
        logger.exception("交互式查询失败")

    console.print("\n[dim]按回车返回主菜单...[/dim]")
    input()


def _interactive_delete(console: Console, app: LiuyaoDecoderApp):
    """交互式删除记录"""
    console.print("\n[bold cyan]删除辩论记录[/bold cyan]")

    try:
        record_id = Prompt.ask("\n请输入要删除的记录ID", type=int)

        # 先显示记录信息
        record = app.database.load_debate(record_id)
        if record:
            hex_data = json.loads(record.hexagram_input)
            ben_gua = hex_data.get('ben_gua_name', '未知')
            bian_gua = hex_data.get('bian_gua_name', '未知')

            console.print(f"\n记录信息:")
            console.print(f"  卦象: {ben_gua} → {bian_gua}")
            console.print(f"  时间: {record.timestamp.strftime('%Y-%m-%d %H:%M')}")
            console.print(f"  收敛: {record.convergence_score:.2f}")

            if Confirm.ask("\n确认删除此记录", default=False):
                app.database.delete_debate(record_id)
                console.print("[green]✅ 已删除[/green]")
            else:
                console.print("[yellow]已取消[/yellow]")
        else:
            console.print(f"[bold red]❌ 未找到记录: {record_id}[/bold red]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 删除失败: {e}[/bold red]")
        logger.exception("交互式删除失败")

    console.print("\n[dim]按回车返回主菜单...[/dim]")
    input()


def _interactive_test_config(console: Console):
    """交互式测试配置"""
    console.print("\n[bold cyan]测试配置[/bold]\n")

    try:
        config = Config()

        # LLM配置
        console.print("[bold]LLM 配置:[/bold]")
        for client_name in ['kimi', 'glm', 'deepseek', 'openai', 'anthropic', 'gemini']:
            client_config = config.get_llm_config(client_name)
            api_key = client_config.get('api_key', '')
            status = "[green]✅[/green]" if api_key else "[red]❌[/red]"
            console.print(f"  {status} {client_name}: {client_config['model']}")

        # Agent配置
        console.print("\n[bold]Agent 配置:[/bold]")
        for agent_name in ['traditional', 'xiangshu', 'mangpai']:
            agent_config = config.get_agent_config(agent_name)
            console.print(f"  {agent_config['school']}: {agent_config['llm_client']} ({agent_config['model']})")

        # 辩论配置
        console.print("\n[bold]辩论配置:[/bold]")
        debate_config = config.get_debate_config()
        console.print(f"  最大轮数: {debate_config['max_rounds']}")
        console.print(f"  收敛阈值: {debate_config['convergence_threshold']}")

        console.print("\n[green]✅ 配置测试完成[/green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 测试失败: {e}[/bold red]")
        logger.exception("交互式测试配置失败")

    console.print("\n[dim]按回车返回主菜单...[/dim]")
    input()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # 运行CLI
    cli()
