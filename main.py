"""六爻解读多Agent系统 - 主入口"""
import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from loguru import logger

from config.config_loader import Config
from utils.parser import HexagramParser
from agents.orchestrator import DebateOrchestrator
from utils.report_generator import ReportGenerator
from storage.models import HexagramInput


console = Console()


class LiuyaoDecoderApp:
    """主应用类 - 协调整个解码流程"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化应用

        Args:
            config_path: 可选的配置文件路径
        """
        try:
            self.config = Config(config_path)
            self.parser = HexagramParser()
            self.orchestrator = DebateOrchestrator(self.config)
            self.report_generator = ReportGenerator()

            logger.info("应用初始化成功")
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            console.print(f"[bold red]应用初始化失败: {e}[/bold red]")
            raise

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

            # Stage 5: 保存到数据库（如果启用，Stage 2实现）
            if save_to_db:
                console.print("[yellow]⚠ 数据库保存功能将在Stage 2实现[/yellow]")
                # record = self.database.save_debate(context, report)
                # console.print(f"✅ 已保存到数据库 (ID: {record.id})")

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
        app = LiuyaoDecoderApp(config)
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
        app = LiuyaoDecoderApp(config)
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
        console.print("[yellow]⚠ 数据库查询功能将在Stage 2实现[/yellow]")

        # Stage 2 实现:
        # app = LiuyaoDecoderApp(config)
        # records = app.database.list_debates(limit=limit, offset=offset)
        #
        # if not records:
        #     console.print("📭 暂无辩论记录")
        #     return 0
        #
        # table = Table(title=f"辩论记录 (共 {len(records)} 条)")
        # table.add_column("ID", style="cyan")
        # table.add_column("时间", style="green")
        # table.add_column("卦象", style="yellow")
        # table.add_column("收敛轮次", style="magenta")
        #
        # for record in records:
        #     table.add_row(
        #         str(record.id),
        #         record.timestamp.strftime('%Y-%m-%d %H:%M'),
        #         record.hexagram_input[:50] + "...",
        #         str(record.convergence_round) or "未收敛"
        #     )
        #
        # console.print(table)

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
        console.print("[yellow]⚠ 数据库查看功能将在Stage 2实现[/yellow]")

        # Stage 2 实现:
        # app = LiuyaoDecoderApp(config)
        # record = app.database.load_debate(debate_id)
        #
        # if not record:
        #     console.print(f"❌ 未找到辩论记录: {debate_id}", style="bold red")
        #     return 1
        #
        # report = record.final_report or "(报告未生成)"
        #
        # if output:
        #     Path(output).write_text(report, encoding='utf-8')
        #     console.print(f"✅ 报告已保存: {output}")
        # else:
        #     console.print(report)

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
        console.print("[yellow]⚠ 数据库删除功能将在Stage 2实现[/yellow]")

        # Stage 2 实现:
        # app = LiuyaoDecoderApp(config)
        # success = app.database.delete_debate(debate_id)
        #
        # if success:
        #     console.print(f"✅ 已删除辩论记录: {debate_id}")
        #     return 0
        # else:
        #     console.print(f"❌ 未找到辩论记录: {debate_id}", style="bold red")
        #     return 1

        return 0

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
