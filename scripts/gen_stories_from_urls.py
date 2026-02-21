#!/usr/bin/env python3
"""gen_stories_from_urls.py
==========================
Gera Stories do Instagram (1080x1920) a partir de uma lista de URLs.

Fluxo:
  1. Lê `items.json` com campos: title, url, subtitle, impact.
  2. Para cada item, abre a URL no Playwright e captura um screenshot
     *acima da dobra* (viewport 1080x1920, sem scroll).
  3. Salva os screenshots em shots/ (ou --shots-dir).
  4. Chama make_story.py para compor o Story final (fundo + overlay + texto).
  5. Grava os PNGs finais no --out-dir.

Uso:
  # dentro do projeto (venv ativo):
  python scripts/gen_stories_from_urls.py \
      --items items.json \
      --shots-dir shots/ \
      --out-dir out/

  # flags opcionais:
  --browser chromium|firefox|webkit  (padrão: chromium)
  --timeout 30000                    (ms por página)
  --skip-screenshots                 (reutiliza shots existentes)

Dependências (venv):
  playwright  +  playwright install chromium
  pillow
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

VIEWPORT_W = 1080
VIEWPORT_H = 1920


def take_screenshot(
    url: str, out_path: Path, browser_type: str, timeout: int
) -> None:
    """Captura o topo da página (above the fold) via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "playwright não encontrado. Execute:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    with sync_playwright() as p:
        factory = {"chromium": p.chromium, "firefox": p.firefox, "webkit": p.webkit}
        browser = factory.get(browser_type, p.chromium).launch(headless=True)
        context = browser.new_context(
            viewport={"width": VIEWPORT_W, "height": VIEWPORT_H},
            device_scale_factor=1,
            user_agent=(
                "Mozilla/5.0 (Linux; Android 12; Pixel 6) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            page.wait_for_timeout(2000)
        except Exception as exc:
            print(f"  [aviso] Erro ao carregar {url}: {exc}", file=sys.stderr)

        # Apenas o viewport visível = acima da dobra
        page.screenshot(
            path=str(out_path),
            clip={"x": 0, "y": 0, "width": VIEWPORT_W, "height": VIEWPORT_H},
        )
        browser.close()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Gera Stories do Instagram a partir de URLs (Playwright + make_story.py)"
    )
    ap.add_argument(
        "--items",
        default="items.json",
        help="JSON com title, url, subtitle, impact (padrão: items.json)",
    )
    ap.add_argument(
        "--shots-dir",
        default="shots",
        help="Pasta para salvar screenshots (padrão: shots/)",
    )
    ap.add_argument(
        "--out-dir",
        default="out",
        help="Pasta de saída dos Stories (padrão: out/)",
    )
    ap.add_argument(
        "--browser",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Motor do Playwright (padrão: chromium)",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Timeout em ms por página (padrão: 30000)",
    )
    ap.add_argument(
        "--skip-screenshots",
        action="store_true",
        help="Pula a captura; usa screenshots já existentes em --shots-dir",
    )
    args = ap.parse_args()

    # ------------------------------------------------------------------
    # 1. Carrega items.json
    # ------------------------------------------------------------------
    items_path = Path(args.items)
    if not items_path.exists():
        sys.exit(f"Arquivo não encontrado: {items_path}")

    items: list[dict] = json.loads(items_path.read_text(encoding="utf-8"))
    if not items:
        sys.exit("items.json está vazio.")

    print(f"→ {len(items)} item(s) carregado(s) de {items_path}")

    shots_dir = Path(args.shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Screenshots
    # ------------------------------------------------------------------
    if args.skip_screenshots:
        print("→ [skip] Reutilizando screenshots existentes em", shots_dir)
    else:
        print(
            f"→ Capturando {len(items)} screenshot(s) "
            f"({args.browser}, {VIEWPORT_W}x{VIEWPORT_H})..."
        )
        for i, item in enumerate(items, start=1):
            url = item.get("url", "").strip()
            if not url:
                print(f"  [aviso] Item {i} sem URL, pulando.", file=sys.stderr)
                continue
            out_path = shots_dir / f"shot_{i:02d}.png"
            print(f"  [{i}/{len(items)}] {url}")
            take_screenshot(url, out_path, args.browser, args.timeout)
            print(f"         → salvo em {out_path}")

    # ------------------------------------------------------------------
    # 3. Monta lista aumentada com campo 'screenshot'
    # ------------------------------------------------------------------
    augmented = []
    for i, item in enumerate(items, start=1):
        shot_path = shots_dir / f"shot_{i:02d}.png"
        if not shot_path.exists():
            sys.exit(
                f"Screenshot ausente: {shot_path}\n"
                "Rode sem --skip-screenshots ou verifique shots/."
            )
        aug = dict(item)
        aug["screenshot"] = str(shot_path)
        augmented.append(aug)

    # ------------------------------------------------------------------
    # 4. Chama make_story.py
    # ------------------------------------------------------------------
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        json.dump(augmented, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name

    make_story = Path(__file__).resolve().parent / "make_story.py"
    if not make_story.exists():
        sys.exit(f"make_story.py não encontrado em {make_story}")

    cmd = [sys.executable, str(make_story), "--in", tmp_path, "--out-dir", str(out_dir)]
    print(f"\n→ Compondo Stories com make_story.py → {out_dir}/")
    result = subprocess.run(cmd, text=True)

    Path(tmp_path).unlink(missing_ok=True)

    if result.returncode != 0:
        sys.exit(f"make_story.py falhou (código {result.returncode})")

    # ------------------------------------------------------------------
    # 5. Resumo
    # ------------------------------------------------------------------
    stories = sorted(out_dir.glob("story_*.png"))
    print(f"\n✅ {len(stories)} Story(ies) gerado(s):")
    for s in stories:
        size_kb = s.stat().st_size // 1024
        print(f"   {s}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
