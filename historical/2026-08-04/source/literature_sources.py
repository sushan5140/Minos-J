"""Primary literature sources validated for Meno-J Experiment 4."""

from __future__ import annotations

from typing import Any


EXPERIMENT_4_LITERATURE: list[dict[str, Any]] = [
    {
        "citation_id": "L1",
        "title": "Conditional Validity of Inductive Conformal Predictors",
        "authors": ["Vladimir Vovk"],
        "year": 2012,
        "venue": "Proceedings of Machine Learning Research 25 (ACML)",
        "url": "https://proceedings.mlr.press/v25/vovk12.html",
        "relevance": (
            "Defines and analyzes conditional inductive conformal prediction, including category-wise "
            "validity and limits of precise object-conditional validity."
        ),
        "validation_method": "Primary PMLR proceedings page retrieved via Jina Reader.",
    },
    {
        "citation_id": "L2",
        "title": "Distribution-Free Predictive Inference For Regression",
        "authors": [
            "Jing Lei",
            "Max G'Sell",
            "Alessandro Rinaldo",
            "Ryan J. Tibshirani",
            "Larry Wasserman",
        ],
        "year": 2018,
        "venue": "Journal of the American Statistical Association",
        "url": "https://arxiv.org/abs/1604.04173",
        "relevance": (
            "Establishes finite-sample marginal coverage for conformal regression and discusses locally "
            "varying interval length under heteroskedasticity."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L3",
        "title": "The limits of distribution-free conditional predictive inference",
        "authors": [
            "Rina Foygel Barber",
            "Emmanuel J. Candès",
            "Aaditya Ramdas",
            "Ryan J. Tibshirani",
        ],
        "year": 2019,
        "venue": "arXiv preprint arXiv:1903.04684",
        "url": "https://arxiv.org/abs/1903.04684",
        "relevance": (
            "Shows why exact distribution-free conditional coverage is generally impossible and studies "
            "relaxations between marginal and conditional guarantees."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L4",
        "title": "Conformal Prediction Under Covariate Shift",
        "authors": [
            "Ryan J. Tibshirani",
            "Rina Foygel Barber",
            "Emmanuel J. Candès",
            "Aaditya Ramdas",
        ],
        "year": 2019,
        "venue": "Advances in Neural Information Processing Systems 32",
        "url": "https://arxiv.org/abs/1904.06019",
        "relevance": (
            "Introduces weighted conformal prediction for covariate shift when test-to-training "
            "likelihood ratios are known or accurately estimated."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L5",
        "title": "Classification with Valid and Adaptive Coverage",
        "authors": ["Yaniv Romano", "Matteo Sesia", "Emmanuel J. Candès"],
        "year": 2020,
        "venue": "Advances in Neural Information Processing Systems 33",
        "url": "https://arxiv.org/abs/2006.02544",
        "relevance": (
            "Introduces adaptive prediction sets and a classification conformity score designed to "
            "improve approximate conditional coverage."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L6",
        "title": "Adaptive Conformal Inference Under Distribution Shift",
        "authors": ["Isaac Gibbs", "Emmanuel J. Candès"],
        "year": 2021,
        "venue": "Advances in Neural Information Processing Systems 34",
        "url": "https://arxiv.org/abs/2106.00170",
        "relevance": (
            "Develops online adaptive conformal inference for time-varying distributions and analyzes "
            "the adaptation-versus-stability tradeoff."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L7",
        "title": "Conformal prediction for time series",
        "authors": ["Chen Xu", "Yao Xie"],
        "year": 2021,
        "venue": "International Conference on Machine Learning (conference version)",
        "url": "https://arxiv.org/abs/2010.09107",
        "relevance": (
            "Develops EnbPI for sequential time-series prediction without requiring exchangeability and "
            "derives conditional and marginal coverage-gap bounds."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
    {
        "citation_id": "L8",
        "title": "Conformal prediction beyond exchangeability",
        "authors": [
            "Rina Foygel Barber",
            "Emmanuel J. Candès",
            "Aaditya Ramdas",
            "Ryan J. Tibshirani",
        ],
        "year": 2023,
        "venue": "Annals of Statistics",
        "url": "https://arxiv.org/abs/2202.13415",
        "relevance": (
            "Uses weighted quantiles and randomization to reduce coverage loss under distribution drift "
            "and nonsymmetric fitting algorithms."
        ),
        "validation_method": "Primary arXiv record retrieved via Jina Reader.",
    },
]
