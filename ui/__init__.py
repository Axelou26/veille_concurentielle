"""
Modules UI pour l'application de veille concurrentielle
Contient les handlers pour chaque onglet de l'application
"""

from .overview_tab import render_overview_tab
from .ai_tab import render_ai_tab
from .stats_tab import render_stats_tab
from .insert_ao_tab import render_insert_ao_tab
from .database_tab import render_database_tab

__all__ = [
    'render_overview_tab',
    'render_ai_tab',
    'render_stats_tab',
    'render_insert_ao_tab',
    'render_database_tab'
]

