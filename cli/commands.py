"""CLI命令定义"""
import asyncio
import json
import re
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from loguru import logger

from core.decoder import LiuyaoDecoder
from config.config_loader import Config
from cli.ui import RichUI

console = Console()


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

        # 创建解码器
        decoder = LiuyaoDecoder(Config(config) if config else None)

        # 创建进度回调
        max_rounds = decoder.config.get_debate_config()['max_rounds']
        progress_callback = RichUI.create_progress_callback(console, max_rounds)

        # 解码
        with console.status("[bold yellow]正在解码..."):
            result = asyncio.run(decoder.decode(
                text=text,
                save_to_db=not no_save,
                output_file=output,
                progress_callback=progress_callback
            ))

        # 显示最终统计
        RichUI.display_final_stats(console, result['context'])

        # 如果没有指定输出文件，打印到控制台
        if not output:
            console.print("\n" + "="*80 + "\n")
            console.print(result['report'])
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
        decoder = LiuyaoDecoder(Config(config) if config else None)
        max_rounds = decoder.config.get_debate_config()['max_rounds']
        progress_callback = RichUI.create_progress_callback(console, max_rounds)

        result = asyncio.run(decoder.decode(
            text=hexagram_text,
            save_to_db=not no_save,
            output_file=output,
            progress_callback=progress_callback
        ))

        RichUI.display_final_stats(console, result['context'])

        if not output:
            console.print("\n" + "="*80 + "\n")
            console.print(result['report'])
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
def list_cmd(limit: int, offset: int, config: Optional[str]):
    """列出历史辩论记录

    示例:
        python main.py list -l 10
        python main.py list --limit 5 --offset 10
    """
    try:
        decoder = LiuyaoDecoder(Config(config) if config else None)
        records = decoder.get_history(limit=limit, offset=offset)
        RichUI.display_history_table(console, records)
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
        decoder = LiuyaoDecoder(Config(config) if config else None)
        record = decoder.get_record(debate_id)

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
        decoder = LiuyaoDecoder(Config(config) if config else None)
        success = decoder.delete_record(debate_id)

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
