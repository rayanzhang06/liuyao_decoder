"""CLI UI显示逻辑"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from loguru import logger


class RichUI:
    """Rich UI 显示类"""

    @staticmethod
    def display_agent_responses(console: Console, responses, title: str):
        """
        显示 Agent 响应摘要

        Args:
            console: Rich Console 对象
            responses: AgentResponse 对象列表
            title: 显示标题
        """
        for resp in responses:
            # 提取核心观点（前200字符）
            content_preview = resp.content[:200] + "..." if len(resp.content) > 200 else resp.content

            # 构建显示文本
            display_text = Text()
            display_text.append(f"{resp.agent_name} ({resp.school}): ", style="bold cyan")
            display_text.append(f"置信度 {resp.confidence}/10\n", style="yellow")
            display_text.append(content_preview, style="white")

            console.print(Panel(display_text, border_style="cyan", padding=(0, 1)))

    @staticmethod
    def display_final_stats(console: Console, context):
        """显示最终统计"""
        stats_table = Table(title="辩论完成", show_header=False)
        stats_table.add_row("总轮次", str(context.current_round))
        stats_table.add_row("收敛分数", f"{context.convergence_score:.2f}")
        stats_table.add_row("状态", context.state.value)
        console.print(stats_table)

    @staticmethod
    def create_progress_callback(console: Console, max_rounds: int):
        """
        创建进度回调函数

        Args:
            console: Rich Console 对象
            max_rounds: 最大轮次

        Returns:
            Callable: 回调函数
        """
        def callback(event_type: str, data: dict):
            if event_type == "parsed":
                hexagram = data.get("hexagram")
                console.print(f"✅ 卦象解析成功: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")

            elif event_type == "initial_done":
                # 显示初始解读结果
                RichUI.display_agent_responses(console, data.get('responses', []), "初始解读")

            elif event_type == "round_start":
                round_num = data.get('round_num')
                console.print(f"[bold cyan]第 {round_num}/{max_rounds} 轮辩论...[/bold cyan]")

            elif event_type == "round_done":
                round_num = data.get('round_num')
                # 显示本轮辩论结果
                RichUI.display_agent_responses(console, data.get('responses', []), f"第 {round_num} 轮")

            elif event_type == "converged":
                reason = data.get('reason')
                console.print(f"[green]✓ 辩论收敛: {reason}[/green]")

        return callback

    @staticmethod
    def display_history_table(console: Console, records):
        """
        显示历史记录表格

        Args:
            console: Rich Console 对象
            records: 记录列表
        """
        import json

        if not records:
            console.print("📭 暂无辩论记录")
            return

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
