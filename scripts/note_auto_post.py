#!/usr/bin/env python3
"""
note.com 自動投稿スクリプト
- ブラウザ操作でnote記事にアイキャッチ画像をアップロード
- 有料ライン設定
- 記事を公開
- 既存の下書き記事にも使える

使い方:
  # 初回: ログインしてセッションを保存
  python3 note_auto_post.py --login

  # アイキャッチ画像をアップロードして公開
  python3 note_auto_post.py --note-id nb135ac55d665 --image /path/to/image.png

  # 有料設定付きで公開
  python3 note_auto_post.py --note-id nb135ac55d665 --image /path/to/image.png --price 300
"""

import argparse
import sys
import os
import time
from pathlib import Path

# Playwrightのインポート
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("❌ Playwrightが未インストールです")
    print("   pip3 install playwright && python3 -m playwright install chromium")
    sys.exit(1)

# セッション保存先
SESSION_DIR = os.path.expanduser("~/.note-session")


def login_and_save_session():
    """ブラウザを開いてnoteにログイン、セッションを保存"""
    print("🔐 noteにログインしてください...")
    print("   ブラウザが開きます。ログイン後、自動的にセッションが保存されます。")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://note.com/login")
        print("   ログイン画面が表示されました。メールとパスワードでログインしてください。")

        # ログイン完了を待つ（投稿ボタンが表示されるまで最大5分待機）
        try:
            print("   ログインが完了するまで待機中...（最大5分）")
            page.wait_for_selector("text=投稿", timeout=300000)
            time.sleep(2)
            print("✅ ログイン成功！セッションを保存中...")
        except PWTimeout:
            print("⏰ タイムアウトしました。もう一度試してください。")
            browser.close()
            return False

        # セッションを保存
        context.storage_state(path=os.path.join(SESSION_DIR, "state.json"))
        browser.close()
        print(f"✅ セッションを保存しました: {SESSION_DIR}/state.json")
        return True


def upload_eyecatch(page, image_path: str):
    """アイキャッチ画像をアップロード"""
    print(f"🖼️  アイキャッチ画像をアップロード中: {image_path}")

    # 画像追加アイコンをクリック
    eyecatch_btn = page.locator("[class*='eyecatch'], [aria-label*='アイキャッチ'], [class*='header-image']").first
    if not eyecatch_btn.is_visible():
        # フォールバック: タイトル上のアイコンを探す
        eyecatch_btn = page.locator("button").filter(has=page.locator("svg")).first

    eyecatch_btn.click()
    time.sleep(1)

    # 「画像をアップロード」メニューが出る
    upload_menu = page.get_by_text("画像をアップロード")
    if upload_menu.is_visible():
        # file inputを直接操作（クリックするとOSダイアログが出るので）
        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(image_path)
        print("   ファイルを設定しました。アップロード待機中...")
        time.sleep(3)
    else:
        # 直接file inputに設定
        file_input = page.locator("input[type='file']").first
        file_input.set_input_files(image_path)
        time.sleep(3)

    # アップロード完了を確認（画像が表示されるまで待つ）
    try:
        page.wait_for_selector("img[src*='note']", timeout=10000)
        print("✅ アイキャッチ画像のアップロード完了")
        return True
    except PWTimeout:
        print("⚠️  画像のアップロードを確認できませんでしたが、続行します")
        return True


def set_paywall(page, price: int = 300):
    """有料設定と有料ラインの設定"""
    print(f"💰 有料設定中（{price}円）...")

    # 「有料」ラジオボタンをクリック
    paid_label = page.get_by_text("有料", exact=True)
    if paid_label.is_visible():
        paid_label.click()
        time.sleep(1)

        # 価格入力
        price_input = page.locator("input[type='number'], input[inputmode='numeric']").first
        if price_input.is_visible():
            price_input.fill(str(price))
            print(f"   価格を{price}円に設定しました")

    return True


def publish_article(page, note_id: str, image_path: str = None, price: int = 0):
    """記事を公開する"""
    edit_url = f"https://editor.note.com/notes/{note_id}/edit/"

    print(f"📝 記事エディタを開いています: {edit_url}")
    page.goto(edit_url)
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    # タイトルが表示されるまで待つ
    try:
        title = page.locator("h1, [class*='title']").first.text_content()
        print(f"   記事タイトル: {title[:50]}...")
    except:
        print("   記事を読み込み中...")
        time.sleep(3)

    # 1. アイキャッチ画像のアップロード
    if image_path:
        try:
            # アイキャッチボタンを探す（class名に sc-131cded0 を含むボタン）
            eyecatch_btn = page.locator("button[class*='sc-131cded0']")
            if eyecatch_btn.count() == 0:
                # フォールバック: 9番目のボタン（エディタツールバーの前）
                eyecatch_btn = page.locator("button").nth(9)

            print("   アイキャッチボタンをクリック中...")
            eyecatch_btn.click()
            time.sleep(2)

            # メニューが出たら「画像をアップロード」をクリック
            upload_text = page.get_by_text("画像をアップロード")
            if upload_text.is_visible():
                print("   アップロードメニューが表示されました")

                # クリックするとfile inputが生成される（まだクリックしない）
                # file_chooserイベントを待ちながらクリック
                with page.expect_file_chooser() as fc_info:
                    upload_text.click()
                file_chooser = fc_info.value
                file_chooser.set_files(image_path)
                print("   画像ファイルを設定しました。クロップモーダル待機中...")
                time.sleep(3)

                # クロップモーダルが表示される場合がある
                crop_modal = page.locator("[class*='CropModal'], [class*='ReactModal__Overlay']")
                if crop_modal.count() > 0:
                    print("   クロップモーダルが表示されました。適用中...")
                    # 「適用」「完了」「OK」ボタンを探す
                    apply_btn = page.get_by_text("適用", exact=True)
                    if not apply_btn.is_visible():
                        apply_btn = page.get_by_text("完了", exact=True)
                    if not apply_btn.is_visible():
                        apply_btn = page.get_by_text("決定", exact=True)
                    if not apply_btn.is_visible():
                        # モーダル内のボタンを探す（キャンセル以外）
                        modal_btns = crop_modal.locator("button")
                        for i in range(modal_btns.count()):
                            btn_text = modal_btns.nth(i).text_content().strip()
                            if btn_text and btn_text != "キャンセル":
                                apply_btn = modal_btns.nth(i)
                                print(f"   モーダルボタン: '{btn_text}'")
                                break

                    if apply_btn.is_visible():
                        apply_btn.click()
                        time.sleep(3)
                        print("✅ クロップを適用しました")
                    else:
                        # ESCで閉じる
                        page.keyboard.press("Escape")
                        time.sleep(2)
                        print("   ESCでモーダルを閉じました")
                else:
                    print("✅ クロップモーダルなし")

                print("✅ アイキャッチ画像をアップロードしました")
                time.sleep(2)
            else:
                print("⚠️  アップロードメニューが表示されませんでした")
        except Exception as e:
            print(f"⚠️  アイキャッチのアップロードに失敗: {e}")
            import traceback
            traceback.print_exc()

    # 2. 公開設定ページへ移動（直接URL遷移が最も確実）
    print("📤 公開設定へ移動中...")
    publish_url = f"https://editor.note.com/notes/{note_id}/publish/"

    # ダイアログが出る場合があるのでハンドラーを設定
    page.on("dialog", lambda dialog: dialog.accept())

    page.goto(publish_url)
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    # ページ上部にスクロール
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    # 3. 有料設定（priceが指定されている場合）
    if price > 0:
        set_paywall(page, price)

    # 4. 投稿/更新ボタンをクリック
    print("🚀 記事を公開中...")

    # ページ上部にスクロール（ボタンが画面外の場合がある）
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    # 「投稿する」か「更新する」ボタンを探す
    submit_btn = None
    for btn_text in ["投稿する", "更新する"]:
        candidate = page.get_by_text(btn_text, exact=True)
        if candidate.is_visible():
            submit_btn = candidate
            print(f"   ボタン「{btn_text}」を見つけました")
            break

    if submit_btn is None:
        # フォールバック: 右上のボタン（index 1が通常「投稿する/更新する」）
        all_btns = page.locator("button")
        if all_btns.count() > 1:
            btn1_text = all_btns.nth(1).text_content().strip()
            if btn1_text in ["投稿する", "更新する"]:
                submit_btn = all_btns.nth(1)
                print(f"   フォールバック: ボタン「{btn1_text}」を見つけました")

    if submit_btn:
        submit_btn.click()
        time.sleep(5)

        # 公開完了ダイアログを確認
        try:
            page.wait_for_selector("text=公開されました", timeout=10000)
            print("🎉 記事が公開されました！")
        except PWTimeout:
            print("✅ 公開/更新ボタンを押しました")

        return True
    else:
        print("❌ 投稿/更新ボタンが見つかりませんでした")
        return False


def take_screenshot(page, filename="debug_screenshot.png"):
    """デバッグ用スクリーンショット"""
    path = os.path.expanduser(f"~/Downloads/{filename}")
    page.screenshot(path=path)
    print(f"📸 スクリーンショット保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="note.com 自動投稿スクリプト")
    parser.add_argument("--login", action="store_true", help="ログインしてセッションを保存")
    parser.add_argument("--note-id", type=str, help="noteの記事ID（例: nb135ac55d665）")
    parser.add_argument("--image", type=str, help="アイキャッチ画像のパス")
    parser.add_argument("--price", type=int, default=0, help="有料記事の価格（0=無料）")
    parser.add_argument("--headless", action="store_true", help="ヘッドレスモードで実行")
    parser.add_argument("--debug", action="store_true", help="デバッグモード（スクショ保存）")

    args = parser.parse_args()

    # セッションディレクトリ作成
    os.makedirs(SESSION_DIR, exist_ok=True)

    # ログインモード
    if args.login:
        login_and_save_session()
        return

    # 記事IDが必要
    if not args.note_id:
        print("❌ --note-id を指定してください")
        print("   例: python3 note_auto_post.py --note-id nb135ac55d665 --image ~/Downloads/eyecatch.png")
        sys.exit(1)

    # セッションファイルの確認
    session_file = os.path.join(SESSION_DIR, "state.json")
    if not os.path.exists(session_file):
        print("❌ セッションファイルがありません。先に --login でログインしてください")
        print("   python3 note_auto_post.py --login")
        sys.exit(1)

    # 画像ファイルの確認
    if args.image and not os.path.exists(args.image):
        print(f"❌ 画像ファイルが見つかりません: {args.image}")
        sys.exit(1)

    # メイン処理
    print("=" * 50)
    print("📝 note.com 自動投稿スクリプト")
    print("=" * 50)

    with sync_playwright() as p:
        # ヘッドレスモードではnoteのメニューが表示されないため、デフォルトはGUIモード
        browser = p.chromium.launch(headless=args.headless, slow_mo=100)
        context = browser.new_context(storage_state=session_file)
        page = context.new_page()

        try:
            success = publish_article(
                page,
                note_id=args.note_id,
                image_path=args.image,
                price=args.price
            )

            if args.debug:
                take_screenshot(page, "note_final_state.png")

            if success:
                print("\n" + "=" * 50)
                print("✅ 完了！")
                print("=" * 50)
            else:
                print("\n❌ 一部の処理が失敗しました。手動で確認してください。")
                take_screenshot(page, "note_error_state.png")

        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            take_screenshot(page, "note_error_state.png")
            raise

        finally:
            # セッションを更新保存
            context.storage_state(path=session_file)
            browser.close()


if __name__ == "__main__":
    main()
