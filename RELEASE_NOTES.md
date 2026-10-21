# ShiftWheel 1.0.0

ShiftWheel — бесплатный локальный конвертер файлов для **macOS (Apple Silicon)** и **Windows 10/11 (x64)**. Начинаете тащить файл, жмёте **Shift**, и вокруг курсора раскрывается круглое меню. Отпускаете файл на нужный сектор — результат появляется рядом с оригиналом. Оригинал не меняется, файлы никуда не отправляются.

Новое в 1.0.0: светлый дизайн меню **Comandos Light**: кремовые секторы, сектор под курсором подсвечивается лаймом, в центре чёрный круг с подсказкой. Старое «жидкое стекло» включается переменной окружения `SHIFTWHEEL_THEME=glass`.

## Что умеет

- **Картинки** (PNG, JPG, WEBP, HEIC, TIFF, AVIF, BMP, GIF, ICO): перевод в любой из этих форматов и в PDF, несколько картинок → один PDF. Инструменты: сжать, изменить размер, обрезать, правка цвета, пометки, замазать, фон, метаданные/GPS.
- **PDF**: в JPG, PNG, DOCX, TXT. Инструменты: сжать, разбить, повернуть, склеить, пароль, извлечь картинки, метаданные.
- **DOCX / TXT / MD / HTML**: в PDF, TXT, DOCX.
- **Видео** (MP4, MOV, M4V, WEBM, MKV, AVI): в MP4, MOV, WEBM, GIF, MP3, M4A, WAV. Сжать (H.264 до 1080p), Small (720p), извлечь звук, склеить несколько файлов.
- **Звук** (MP3, WAV, M4A, AAC, FLAC, OGG, OPUS, AIFF): в MP3, M4A, WAV, склеить.

## Файлы релиза

| Файл | Для чего |
|---|---|
| `ShiftWheel-arm64.dmg` | Mac на M1/M2/M3/M4 — образ диска |
| `ShiftWheel-arm64.app.zip` | то же приложение в zip |
| `ShiftWheel-windows-x64.zip` | Windows 10/11, 64 бита |
| Source code (zip / tar.gz) | исходники |

## Установка на Mac

1. Откройте `ShiftWheel-arm64.dmg` и перетащите **ShiftWheel** в «Программы».
2. Приложение не подписано сертификатом Apple, поэтому снимите карантин:
   ```bash
   xattr -cr /Applications/ShiftWheel.app
   ```
   Или: **Системные настройки → Конфиденциальность и безопасность → «Всё равно открыть»**.
3. ShiftWheel живёт в строке меню, иконки в Dock нет. Особых разрешений не требуется. Если меню по Shift не появляется — добавьте ShiftWheel в «Универсальный доступ» и перезапустите.

## Установка на Windows

1. Распакуйте `ShiftWheel-windows-x64.zip`, например в `%LOCALAPPDATA%\Programs\ShiftWheel`, и запустите `ShiftWheel.exe`.
2. Если SmartScreen пишет «Windows защитила ваш компьютер» — **Подробнее → Выполнить в любом случае**.
3. ShiftWheel живёт в области уведомлений рядом с часами.

## ffmpeg (для видео и звука)

ffmpeg не встроен в приложение — поставьте его один раз:

- Mac: `brew install ffmpeg`
- Windows: `winget install Gyan.FFmpeg` (или `choco install ffmpeg`, `scoop install ffmpeg`)

ShiftWheel находит ffmpeg сам: `SHIFTWHEEL_FFMPEG`, папка приложения, Homebrew / winget / Chocolatey / Scoop, `PATH`.

## Ограничения

- Сборки не подписаны (Apple Developer ID / Authenticode): при первом запуске будут предупреждения Gatekeeper и SmartScreen.
- Только Apple Silicon и Windows x64; Intel Mac и Windows ARM не собираются.
- На Windows — только zip: нет установщика, пункта в «Пуске» и в контекстном меню Проводника.
- Склейка (Join) работает без перекодирования — файлы должны совпадать по кодеку, размеру и частоте кадров.
- Обрезки видео по времени в меню пока нет; для длинных видео нет индикатора прогресса.
- GIF из видео: до 12 кадров/с и до 640 px по ширине.

ShiftWheel — форк [DragShift](https://github.com/llamaboi55/DragShift) (MIT). Лицензия и авторство — в `LICENSE` и `NOTICE.md`.
