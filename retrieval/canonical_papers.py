"""
Canonical classic paper registry for fallback retrieval.
Guarantees verified real metadata for landmark foundational papers.
"""

from typing import List
from retrieval.base import Document

CANONICAL_PAPERS: List[Document] = [
    Document(
        id="arxiv_1706_03762",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"],
        abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose the Transformer, a model architecture eschewing recurrence and instead relying entirely on an attention mechanism to draw global dependencies between input and output.",
        url="https://arxiv.org/abs/1706.03762",
        published="2017",
        source="arXiv",
        doi="10.48550/arXiv.1706.03762",
        arxiv_id="1706.03762",
        content="Title: Attention Is All You Need\nAuthors: Ashish Vaswani et al.\nAbstract: We propose the Transformer, a novel architecture relying entirely on self-attention mechanisms."
    ),
    Document(
        id="arxiv_1810_04805",
        title="BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        authors=["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
        abstract="We introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers.",
        url="https://arxiv.org/abs/1810.04805",
        published="2018",
        source="arXiv",
        doi="10.48550/arXiv.1810.04805",
        arxiv_id="1810.04805",
        content="Title: BERT: Pre-training of Deep Bidirectional Transformers\nAuthors: Jacob Devlin et al.\nAbstract: Bidirectional Encoder Representations from Transformers."
    ),
    Document(
        id="arxiv_1512_03385",
        title="Deep Residual Learning for Image Recognition",
        authors=["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
        abstract="Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those used previously. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
        url="https://arxiv.org/abs/1512.03385",
        published="2015",
        source="arXiv",
        doi="10.48550/arXiv.1512.03385",
        arxiv_id="1512.03385",
        content="Title: Deep Residual Learning for Image Recognition\nAuthors: Kaiming He et al.\nAbstract: Deep Residual Networks (ResNet)."
    )
]


def get_canonical_papers() -> List[Document]:
    """Return landmark canonical papers."""
    return list(CANONICAL_PAPERS)
