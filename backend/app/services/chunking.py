"""
Text chunking utilities for RAG.
将长文本分块以适应 embedding 模型的限制并提高检索精度。
"""
from typing import List
import re


class TextChunker:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = 500,      # 每块字符数
        chunk_overlap: int = 50,    # 块之间重叠字符数
        separators: List[str] = None
    ):
        """
        初始化分块器

        Args:
            chunk_size: 每块最大字符数
            chunk_overlap: 相邻块之间重叠的字符数（保持语义连贯性）
            separators: 分割符优先级列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # 段落分隔
            "\n",    # 行分隔
            "。",    # 句子分隔（中文）
            ".",     # 句子分隔（英文）
            " ",     # 词分隔
            ""       # 字符分隔（最后手段）
        ]

    def split_text(self, text: str) -> List[str]:
        """
        将文本分块

        Args:
            text: 原始文本

        Returns:
            分块后的文本列表
        """
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        current_chunk = ""

        # 按优先级尝试不同的分隔符
        for separator in self.separators:
            if separator == "":
                # 最后手段：强制按字符分割
                chunks = self._split_by_chars(text)
                break

            parts = text.split(separator)

            for i, part in enumerate(parts):
                # 加上分隔符（除了最后一个部分）
                if i < len(parts) - 1:
                    part = part + separator

                # 如果单个部分就超过限制，需要进一步分割
                if len(part) > self.chunk_size:
                    continue  # 尝试下一个分隔符

                # 累积到当前块
                if len(current_chunk) + len(part) <= self.chunk_size:
                    current_chunk += part
                else:
                    # 当前块已满，保存并开始新块
                    if current_chunk:
                        chunks.append(current_chunk.strip())

                    # 新块包含重叠部分
                    if self.chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + part
                    else:
                        current_chunk = part

            # 保存最后一块
            if current_chunk:
                chunks.append(current_chunk.strip())

            # 如果成功分块，退出循环
            if chunks:
                break

        return [chunk for chunk in chunks if chunk.strip()]

    def _split_by_chars(self, text: str) -> List[str]:
        """按字符强制分割（保证不超过 chunk_size）"""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    def smart_split_markdown(self, text: str) -> List[str]:
        """
        智能分割 Markdown 文本
        按标题层级分割，保持结构完整性
        """
        # 按 Markdown 标题分割
        sections = re.split(r'(^#+\s+.+$)', text, flags=re.MULTILINE)

        chunks = []
        current_chunk = ""
        current_header = ""

        for i, section in enumerate(sections):
            # 检测是否为标题
            if re.match(r'^#+\s+', section):
                current_header = section
                continue

            # 内容部分
            content = section.strip()
            if not content:
                continue

            # 带标题的完整内容
            full_section = f"{current_header}\n{content}".strip()

            # 如果单个 section 太大，需要分块
            if len(full_section) > self.chunk_size:
                # 递归分割内容部分
                sub_chunks = self.split_text(content)
                for sub_chunk in sub_chunks:
                    chunks.append(f"{current_header}\n{sub_chunk}".strip())
            else:
                # 检查是否能和当前块合并
                if len(current_chunk) + len(full_section) <= self.chunk_size:
                    current_chunk += "\n\n" + full_section if current_chunk else full_section
                else:
                    # 保存当前块，开始新块
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = full_section

        # 保存最后一块
        if current_chunk:
            chunks.append(current_chunk)

        return [chunk for chunk in chunks if chunk.strip()]


# 工厂函数
def get_chunker(chunk_size: int = 500, chunk_overlap: int = 50) -> TextChunker:
    """获取文本分块器实例"""
    return TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
