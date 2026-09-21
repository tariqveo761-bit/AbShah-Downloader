import flet as ft
import yt_dlp
import threading
import re

try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    ffmpeg_exe = None

def main(page: ft.Page):
    page.title = "Ab.Shah Downloader"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0B0F19"
    page.window_width = 450
    page.window_height = 850
    page.window_resizable = False
    page.padding = 18
    page.scroll = ft.ScrollMode.ADAPTIVE

    header = ft.Container(
        content=ft.Text("Ab.Shah Downloader", size=24, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
        alignment=ft.alignment.center,
        margin=ft.margin.only(top=5, bottom=12)
    )

    url_input = ft.TextField(
        hint_text="Paste any video or audio link here...",
        border_radius=14,
        border_color="#1E293B",
        focused_border_color="#00F0FF",
        bgcolor="#111827",
        text_size=13,
        color="#FFFFFF",
        prefix_icon=ft.icons.LINK_ROUNDED,
        content_padding=14
    )

    status_text = ft.Text(value="", size=12, color="#94A3B8", text_align=ft.TextAlign.CENTER)

    neon_ring = ft.Container(
        width=190,
        height=190,
        border_radius=95,
        gradient=ft.SweepGradient(
            colors=["#00F0FF", "#8B5CF6", "#EC4899", "#F59E0B", "#00F0FF"],
            start_angle=0,
            end_angle=6.28
        ),
        visible=False,
        rotate=ft.Rotate(0),
        animate_rotation=ft.Animation(450, ft.AnimationCurve.LINEAR),
        alignment=ft.alignment.center
    )

    inner_btn = ft.Container(
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            controls=[
                ft.Icon(ft.icons.ARROW_DOWNWARD_ROUNDED, size=52, color="#0B0F19"),
                ft.Text("DOWNLOAD", size=16, weight=ft.FontWeight.BOLD, color="#0B0F19")
            ]
        ),
        width=165,
        height=165,
        border_radius=82,
        bgcolor="#00F0FF",
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(spread_radius=2, blur_radius=25, color="#00F0FF66")
    )

    center_btn_stack = ft.Container(
        content=ft.Stack(
            width=190,
            height=190,
            controls=[
                neon_ring,
                ft.Container(content=inner_btn, padding=12, on_click=lambda e: analyze_link(e))
            ]
        ),
        visible=True,
        margin=ft.margin.symmetric(vertical=15)
    )

    history_list = ft.Column(spacing=10)
    history_box = ft.Container(
        bgcolor="#111827",
        border_radius=16,
        padding=14,
        border=ft.border.all(1.5, "#00F0FF44"),
        visible=False,
        content=ft.Column(
            spacing=10,
            controls=[
                ft.Row([
                    ft.Icon(ft.icons.DOWNLOAD_FOR_OFFLINE_ROUNDED, color="#00F0FF", size=20),
                    ft.Text("Download Tasks & History", size=14, weight=ft.FontWeight.BOLD, color="#FFFFFF")
                ]),
                ft.Divider(color="#1E293B", height=1),
                history_list
            ]
        )
    )

    thumb_img = ft.Image(src="", width=400, height=200, fit=ft.ImageFit.COVER, border_radius=14)
    media_title = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF", max_lines=2, overflow=ft.TextOverflow.ELLIPSIS)
    quality_chips_row = ft.Row(wrap=True, spacing=10)

    result_card = ft.Container(
        bgcolor="#111827",
        border_radius=16,
        padding=16,
        border=ft.border.all(1, "#1E293B"),
        visible=False,
        content=ft.Column(
            spacing=12,
            controls=[
                thumb_img,
                media_title,
                ft.Divider(color="#1E293B", height=1),
                ft.Text("Select Available Quality to Download:", size=12, weight=ft.FontWeight.BOLD, color="#00F0FF"),
                quality_chips_row
            ]
        )
    )

    is_animating = [False]
    def run_neon_animation():
        while is_animating[0]:
            neon_ring.rotate.angle += 3.14
            page.update()
            import time
            time.sleep(0.15)

    def start_download_task(target_url, chosen_fid, is_audio=False):
        result_card.visible = False
        history_box.visible = True
        status_text.value = "Downloading started..."
        status_text.color = "#00F0FF"

        task_title = ft.Text("Connecting to stream...", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF", max_lines=1)
        speed_text = ft.Text("Starting...", size=11, color="#00F0FF")
        size_info = ft.Text("0 MB / 0 MB", size=11, color="#94A3B8")
        percent_text = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD, color="#10B981")
        progress_ribbon = ft.ProgressBar(value=0, color="#00F0FF", bgcolor="#1E293B", height=8)
        
        task_card = ft.Container(
            bgcolor="#1F2937",
            border_radius=12,
            padding=12,
            border=ft.border.all(1, "#374151"),
            content=ft.Column(
                spacing=8,
                controls=[
                    task_title,
                    progress_ribbon,
                    ft.Row([speed_text, size_info, percent_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]
            )
        )
        history_list.controls.insert(0, task_card)
        page.update()

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                    downloaded = d.get('downloaded_bytes', 0)
                    pct = downloaded / total
                    progress_ribbon.value = pct
                    percent_text.value = f"{int(pct * 100)}%"

                    down_mb = downloaded / (1024 * 1024)
                    tot_mb = total / (1024 * 1024)
                    size_info.value = f"{down_mb:.1f} MB / {tot_mb:.1f} MB"

                    spd = d.get('speed')
                    if spd:
                        if spd > 1024 * 1024:
                            speed_text.value = f"{spd / (1024*1024):.2f} MB/s"
                        else:
                            speed_text.value = f"{spd / 1024:.0f} KB/s"
                    page.update()
                except Exception:
                    pass
            elif d['status'] == 'finished':
                progress_ribbon.value = 1
                progress_ribbon.color = "#10B981"
                speed_text.value = "Completed"
                speed_text.color = "#10B981"
                percent_text.value = "100%"
                status_text.value = "Download completed successfully!"
                status_text.color = "#10B981"
                page.update()

        def _runner():
            # Universal Web & Multi-Platform Compatible Engine
            ydl_opts = {
                'outtmpl': '%(title)s.%(ext)s',
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'quiet': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            }

            if ffmpeg_exe:
                ydl_opts['ffmpeg_location'] = ffmpeg_exe

            if is_audio:
                ydl_opts['format'] = 'bestaudio/best'
            else:
                ydl_opts['format'] = f"{chosen_fid}+bestaudio/best" if chosen_fid else 'bestvideo+bestaudio/best'

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=True)
                    task_title.value = info.get('title', 'Downloaded Media')[:35]
                    page.update()
            except Exception as err:
                speed_text.value = "Failed"
                speed_text.color = "#EF4444"
                status_text.value = f"Error: {str(err)[:45]}"
                status_text.color = "#EF4444"
                page.update()

        threading.Thread(target=_runner).start()

    def analyze_link(e):
        link = url_input.value.strip() if url_input.value else ""
        if not link:
            try:
                clip = page.get_clipboard()
                if clip and ("http://" in clip or "https://" in clip):
                    url_input.value = clip.strip()
                    link = url_input.value
                    page.update()
            except Exception:
                pass

        if not link:
            status_text.value = "Please paste a valid media link!"
            status_text.color = "#EF4444"
            page.update()
            return

        link = re.sub(r'&list=[^&]+', '', link)
        link = re.sub(r'&start_radio=[^&]+', '', link)

        neon_ring.visible = True
        is_animating[0] = True
        threading.Thread(target=run_neon_animation, daemon=True).start()

        status_text.value = "Scanning all available qualities..."
        status_text.color = "#00F0FF"
        result_card.visible = False
        history_box.visible = False
        quality_chips_row.controls.clear()
        page.update()

        def _fetch():
            try:
                opts = {
                    'quiet': True,
                    'noplaylist': True,
                    'skip_download': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
                }
                if ffmpeg_exe:
                    opts['ffmpeg_location'] = ffmpeg_exe

                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(link, download=False)

                thumb_img.src = info.get('thumbnail', '')
                media_title.value = info.get('title', 'Media File')

                # Universal Audio Button
                audio_btn = ft.ElevatedButton(
                    text="Audio MP3",
                    icon=ft.icons.MUSIC_NOTE_ROUNDED,
                    bgcolor="#10B981",
                    color="#FFFFFF",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    on_click=lambda _: start_download_task(link, None, is_audio=True)
                )
                quality_chips_row.controls.append(audio_btn)

                # Universal Resolution Parser (Har website ke video formats scan honge)
                formats = info.get('formats', [])
                resolutions = {}

                for f in formats:
                    # Height check + direct URL confirmation
                    h = f.get('height')
                    fid = f.get('format_id')
                    url_found = f.get('url') or f.get('fragment_base_url')

                    # Audio-only streams ko video chip mein na daalein
                    if h and h >= 144 and f.get('vcodec') != 'none' and url_found:
                        if h not in resolutions:
                            resolutions[h] = fid

                # Agar specific formats na milein to standard fallback
                if not resolutions:
                    for f in formats:
                        h = f.get('height')
                        fid = f.get('format_id')
                        if h and h not in resolutions:
                            resolutions[h] = fid

                # High to Low Sort (8K down to 360p)
                for h in sorted(resolutions.keys(), reverse=True):
                    fid = resolutions[h]
                    tag = "8K" if h >= 4320 else "4K" if h >= 2160 else "2K" if h >= 1440 else "1080p FHD" if h == 1080 else f"{h}p HD" if h >= 720 else f"{h}p SD"
                    
                    v_btn = ft.ElevatedButton(
                        text=tag,
                        icon=ft.icons.VIDEOCAM_ROUNDED,
                        bgcolor="#1E293B",
                        color="#00F0FF",
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                        on_click=lambda _, f_id=fid: start_download_task(link, f_id, is_audio=False)
                    )
                    quality_chips_row.controls.append(v_btn)

                center_btn_stack.visible = False
                result_card.visible = True
                status_text.value = ""

            except Exception as err:
                status_text.value = f"Scan Error: {str(err)[:50]}"
                status_text.color = "#EF4444"

            is_animating[0] = False
            neon_ring.visible = False
            page.update()

        threading.Thread(target=_fetch).start()

    footer = ft.Container(
        content=ft.Text("Created by Abu Bakkar Shah", size=11, color="#64748B", weight=ft.FontWeight.W_500),
        alignment=ft.alignment.center,
        margin=ft.margin.only(top=30, bottom=15)
    )

    page.add(
        header,
        url_input,
        ft.Row([center_btn_stack], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([status_text], alignment=ft.MainAxisAlignment.CENTER),
        result_card,
        history_box,
        footer
    )

ft.app(target=main)