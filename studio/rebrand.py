#!/usr/bin/env python3
"""Apply the arqam (Creative Studio) branding on top of upstream GridCraft.

Only user-visible text is rebranded; crate names, the file format and other internals keep their
upstream names so `git merge upstream/main` stays easy. The script is idempotent: after merging
upstream, resolve any conflicts in favour of upstream and run it again.

    python3 studio/rebrand.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = 'arqam'
REPO = 'https://github.com/7mz410/CreativeStudio-arqam'
SITE = 'https://studio.creative.ps'
APP_SITE = 'https://arqam.studio.creative.ps'
# Persisted names and legal lines; renaming them would lose settings or misstate copyright.
KEEP = ('by the ArtCraft team', 'Application Support/GridCraft', '/roaming/GridCraft', 'the GridCraft authors', 'GridCraft contributors', 'GRIDCRAFT_')

# (file, upstream text, our text[, marker meaning "already applied"]). The upstream text may also
# be found in its renamed form (after the general rename below).
RULES = [
    # About and the Help menu: our links, no Discord.
    ('crates/ui-egui/src/dialogs.rs', '"A clean-room, open-source, Rust-native spreadsheet. Part of ArtCraft."',
     '"A clean-room, open-source, Rust-native spreadsheet. Part of the Creative Studio suite, built on GridCraft by the ArtCraft team."'),
    ('crates/ui-egui/src/dialogs.rs', 'ui.hyperlink_to("getartcraft.com/apps/gridcraft", "https://getartcraft.com/apps/gridcraft");',
     f'ui.hyperlink_to("arqam.studio.creative.ps", "{APP_SITE}");'),
    ('crates/ui-egui/src/dialogs.rs', 'ui.hyperlink_to("Join the ArtCraft Discord", "https://discord.gg/artcraft");',
     f'ui.hyperlink_to("Source code: github.com/7mz410/CreativeStudio-arqam", "{REPO}");'),
    ('apps/gridcraft/src/native_menu.rs', '("GridCraft on getartcraft.com", "url:https://getartcraft.com/apps/gridcraft", None),',
     f'("arqam on studio.creative.ps", "url:{APP_SITE}", None),'),
    ('apps/gridcraft/src/native_menu.rs', '("Join the ArtCraft Discord…", "url:https://discord.gg/artcraft", None),',
     f'("Creative Studio…", "url:{SITE}", None),'),
    # Web page and packages.
    ('apps/gridcraft-web/index.html', '<title>GridCraft</title>', f'<title>{NAME}</title>'),
    ('apps/gridcraft-web/index.html', 'Loading GridCraft&hellip;', f'Loading {NAME}&hellip;', 'ss-scene'),  # or the splash
    ('packaging/macos/Info.plist.in', '<string>ai.storyteller.gridcraft</string>', '<string>ps.creative.studio.arqam</string>'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPURLINFOABOUT" Value="https://getartcraft.com/apps/gridcraft" />', f'<Property Id="ARPURLINFOABOUT" Value="{APP_SITE}" />'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPURLUPDATEINFO" Value="https://getartcraft.com/apps/gridcraft" />', f'<Property Id="ARPURLUPDATEINFO" Value="{REPO}/releases" />'),
    ('packaging/windows/gridcraft.wxs', '<Property Id="ARPHELPLINK" Value="https://discord.gg/artcraft" />', f'<Property Id="ARPHELPLINK" Value="{REPO}/issues" />'),
    ('packaging/linux/nfpm.yaml', 'homepage: https://getartcraft.com/apps/gridcraft', f'homepage: {APP_SITE}'),
]
# Text in string literals and catalogs, before the general rename.
LITERALS = []
STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


def rename(lit: str) -> str:
    for a, b in LITERALS:
        lit = lit.replace(a, b)
    if any(k in lit for k in KEEP):
        return lit
    return lit.replace('GridCraft', NAME)


def renamed_code(text: str) -> str:
    return STRING.sub(lambda m: rename(m.group(0)), text)


def apply_rules() -> list:
    changed = []
    for rel, a, b, *marker in RULES:
        p = ROOT / rel
        s = p.read_text(encoding='utf-8')
        if marker and marker[0] in s:
            continue
        if a not in s and renamed_code(a) in s:
            a = renamed_code(a)  # the general rename got there first
        if a not in s or (b and a in b and b in s):
            if not b or b in s or renamed_code(b) in s:
                continue  # already applied
            print(f'warning: {rel}: upstream text not found (did upstream change it?): {a[:70]!r}')
            continue
        p.write_text(s.replace(a, b), encoding='utf-8')
        changed.append(rel)
    return changed


def rename_sources() -> list:
    changed = []
    for p in sorted((ROOT / 'crates/ui-egui').rglob('*.rs')) + [q for q in sorted((ROOT / 'crates/engine').rglob('*.rs')) if not q.name.startswith('tests')] + sorted((ROOT / 'apps').rglob('*.rs')):
        s = p.read_text(encoding='utf-8')
        o = renamed_code(s)
        if o != s:
            p.write_text(o, encoding='utf-8')
            changed.append(p.relative_to(ROOT).as_posix())
    # Catalog rows are `context<TAB>English<TAB>translation`: rename both text columns alike.
    for p in sorted((ROOT / 'crates/ui-egui/src/i18n').glob('*.tsv')):
        s = p.read_text(encoding='utf-8')
        rows = []
        for line in s.split('\n'):
            cells = line.split('\t')
            if len(cells) >= 3 and not line.startswith('#'):
                line = '\t'.join([cells[0], *(rename(c) for c in cells[1:])])
            rows.append(line)
        o = '\n'.join(rows)
        if o != s:
            p.write_text(o, encoding='utf-8')
            changed.append(p.relative_to(ROOT).as_posix())
    plist = ROOT / 'packaging/macos/Info.plist.in'
    s = plist.read_text(encoding='utf-8')
    o = re.sub(r'(<key>CFBundle(?:Display|Executable)?Name</key>\s*<string>)GridCraft(</string>)', rf'\g<1>{NAME}\2', s)
    if o != s:
        plist.write_text(o, encoding='utf-8')
        changed.append('packaging/macos/Info.plist.in')
    return changed


def main():
    changed = apply_rules() + rename_sources()
    for c in sorted(set(changed)):
        print('rebranded', c)


if __name__ == '__main__':
    main()
