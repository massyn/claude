"""Stroke icons (24px grid, drawn with currentColor) for templates and page scripts.

Templates draw one with the `icon` macro in templates/partials/icons.html. The app factory exposes
ICONS as the `icon_paths` Jinja global. Paths only: the <svg> markup lives in the macro.
Add app-specific icons to APP_ICONS rather than editing the shared set.
"""

UI_ICONS = {
    # Tab bar
    'home': 'M3 11l9-8 9 8M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5',
    'user': 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
    'users': 'M9 11.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7'
    'M17.5 14.2A6.5 6.5 0 0 1 21.5 20',
    'help': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14M12 17.5v.01',
    'info': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.5v.01',
    'login': 'M10 17l5-5-5-5M15 12H3M14 4h5a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-5',
    'logout': 'M14 17l5-5-5-5M19 12H7M10 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h5',
    'folder': 'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z',
    # Actions
    'back': 'M15 18l-6-6 6-6',
    'chevron': 'M9 18l6-6-6-6',
    'caret': 'M6 9l6 6 6-6',
    'up': 'M12 19V5M6 11l6-6 6 6',
    'down': 'M12 5v14M6 13l6 6 6-6',
    'plus': 'M12 5v14M5 12h14',
    'close': 'M6 6l12 12M18 6L6 18',
    'check': 'M5 12l5 5 9-10',
    'edit': 'M4 20h4L19 9l-4-4L4 16zM13.5 6.5l4 4',
    'more': 'M5 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM12 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z'
    'M19 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z',
    'search': 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4',
    'share': 'M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M16 6l-4-4-4 4M12 2v13',
    'link': 'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',
    'download': 'M12 3v12M7 10l5 5 5-5M5 21h14',
    'upload': 'M12 21V9M7 14l5-5 5 5M5 3h14',
    'message': 'M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.2A8 8 0 1 1 21 12z',
    'navigate': 'M3 11l19-9-9 19-2-8-8-2z',
    'pin': 'M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    'clock': 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
    'rss': 'M5 11a8 8 0 0 1 8 8M5 5a14 14 0 0 1 14 14M6 19h.01',
}

APP_ICONS: dict[str, str] = {}

ICONS = {**UI_ICONS, **APP_ICONS}
