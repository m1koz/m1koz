"""Render profile cards from two public distribution repositories; no app source or private data."""
from datetime import datetime, timezone
from html import escape
from pathlib import Path
import json
import subprocess

PROJECTS = ('m1koz/audio-mixer', 'm1koz/betternotes')

def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', path], text=True))

def main():
    stars = releases = downloads = 0
    for project in PROJECTS:
        info = api('repos/' + project)
        if info['private']:
            raise RuntimeError('Only public project metadata may be used')
        stars += info['stargazers_count']
        page = 1
        while True:
            batch = api(f'repos/{project}/releases?per_page=100&page={page}')
            for release in batch:
                if release['draft'] or release['prerelease']:
                    continue
                releases += 1
                downloads += sum(asset['download_count'] for asset in release['assets']
                                 if asset['name'].lower().endswith(('.dmg', '.exe', '.zip')))
            if len(batch) < 100:
                break
            page += 1
    values = [(str(len(PROJECTS)), 'PUBLIC PROJECTS'), (str(stars), 'PROJECT STARS'),
              (str(releases), 'RELEASES'), (f'{downloads:,}', 'FILE DOWNLOADS')]
    output = Path('dist')
    output.mkdir(exist_ok=True)
    for theme, colors in {
        'dark': ('#0d1117', '#30363d', '#e6edf3', '#9198a1', '#79c0ff'),
        'light': ('#ffffff', '#d1d9e0', '#1f2328', '#59636e', '#0969da'),
    }.items():
        bg, border, fg, muted, accent = colors
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="184" viewBox="0 0 760 184" role="img" aria-labelledby="title desc">',
                 '<title id="title">Public project activity</title>',
                 f'<desc id="desc">{len(PROJECTS)} public projects, {stars} project stars, {releases} releases, {downloads} installer and archive downloads. Downloads count files, not unique users.</desc>',
                 f'<rect x=".5" y=".5" width="759" height="183" rx="16" fill="{bg}" stroke="{border}"/>',
                 '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif">',
                 f'<text x="28" y="32" fill="{muted}" font-size="11" letter-spacing="2">PROJECT ACTIVITY</text>']
        for i, (value, label) in enumerate(values):
            x = 28 + i * 184
            if i:
                parts.append(f'<path d="M{x-16} 55V122" stroke="{border}"/>')
            parts += [f'<text x="{x}" y="94" fill="{accent}" font-size="34" font-weight="650">{escape(value)}</text>',
                      f'<text x="{x}" y="119" fill="{fg}" font-size="10" letter-spacing=".7">{label}</text>']
        updated = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        parts += [f'<text x="28" y="160" fill="{muted}" font-size="10">Public releases · Downloads count files, not unique users</text>',
                  f'<text x="732" y="160" fill="{muted}" font-size="10" text-anchor="end">Updated {updated}</text>',
                  '</g></svg>']
        (output / f'stats-{theme}.svg').write_text('\n'.join(parts) + '\n', encoding='utf-8')
    print(f'Public metrics: {len(PROJECTS)} projects, {stars} stars, {releases} releases, {downloads} file downloads')

if __name__ == '__main__':
    main()
