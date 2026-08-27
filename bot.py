import io
import os
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("learning-report-bot")

REPORT_CHANNEL_NAME = os.getenv("REPORT_CHANNEL_NAME", "daily-standup")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
GOOGLE_SHEETS_WORKSHEET_NAME = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Laporan")
GOOGLE_OAUTH_CLIENT_SECRET_FILE = os.getenv(
    "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
    "/root/discord-learning-report-bot/google-client-secret.json",
)
GOOGLE_OAUTH_TOKEN_FILE = os.getenv(
    "GOOGLE_OAUTH_TOKEN_FILE",
    "/root/discord-learning-report-bot/google-token.json",
)
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
MAX_AUTOCOMPLETE_CHOICES = 25

if not TOKEN:
    raise RuntimeError(
        "Environment variable DISCORD_BOT_TOKEN belum di-set. "
        "Isi token bot Discord Anda di environment terlebih dahulu."
    )


@dataclass
class ReportHeader:
    tanggal: str
    kelas: str
    materi: str
    durasi: str
    jumlah_hadir: str


@dataclass
class ReportRow:
    tanggal: str
    kelas: str
    materi: str
    durasi: str
    jumlah_hadir: str
    aktivitas: str
    hasil: str
    kendala: str
    tindak_lanjut: str
    dikirim_oleh: str
    server_discord: str

    @property
    def parsed_date(self) -> datetime:
        return datetime.strptime(self.tanggal, "%d-%m-%Y")


class GoogleSheetsLogger:
    def __init__(self) -> None:
        self.spreadsheet_id = GOOGLE_SHEETS_SPREADSHEET_ID
        self.worksheet_name = GOOGLE_SHEETS_WORKSHEET_NAME
        self.client_secret_file = GOOGLE_OAUTH_CLIENT_SECRET_FILE
        self.token_file = GOOGLE_OAUTH_TOKEN_FILE
        self.enabled = bool(self.spreadsheet_id)
        self._service = None

    def _build_credentials(self) -> Credentials:
        creds = None

        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, GOOGLE_SCOPES)

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())
            return creds

        if not os.path.exists(self.client_secret_file):
            raise RuntimeError(
                "File OAuth client secret Google tidak ditemukan. "
                f"Harus ada di: {self.client_secret_file}"
            )

        raise RuntimeError(
            "Google OAuth belum diotorisasi. Jalankan file authorize_google.py terlebih dahulu "
            "untuk membuat token Google Sheets."
        )

    def _get_service(self):
        if self._service is None:
            credentials = self._build_credentials()
            self._service = build("sheets", "v4", credentials=credentials)
        return self._service

    def append_report(self, report: ReportRow) -> bool:
        if not self.enabled:
            logger.info("Google Sheets append dilewati karena spreadsheet ID belum diisi.")
            return False

        values = [[
            report.tanggal,
            report.kelas,
            report.materi,
            report.durasi,
            report.jumlah_hadir,
            report.aktivitas,
            report.hasil,
            report.kendala,
            report.tindak_lanjut,
            report.dikirim_oleh,
            report.server_discord,
        ]]

        service = self._get_service()
        service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.worksheet_name}!A:K",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        ).execute()
        return True

    def read_reports(self) -> list[ReportRow]:
        if not self.enabled:
            return []

        service = self._get_service()
        values = service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=f"{self.worksheet_name}!A2:K",
        ).execute().get("values", [])

        reports: list[ReportRow] = []
        for row in values:
            if not row or len(row) < 9:
                continue
            padded = row + [""] * (11 - len(row))
            tanggal = padded[0].strip()
            if not tanggal:
                continue
            try:
                validate_tanggal(tanggal)
            except ValueError:
                continue
            reports.append(
                ReportRow(
                    tanggal=tanggal,
                    kelas=padded[1].strip(),
                    materi=padded[2].strip(),
                    durasi=padded[3].strip(),
                    jumlah_hadir=padded[4].strip(),
                    aktivitas=padded[5].strip(),
                    hasil=padded[6].strip(),
                    kendala=padded[7].strip(),
                    tindak_lanjut=padded[8].strip(),
                    dikirim_oleh=padded[9].strip(),
                    server_discord=padded[10].strip(),
                )
            )
        return reports

    def get_unique_kelas(self) -> list[str]:
        kelas_values = sorted(
            {
                report.kelas
                for report in self.read_reports()
                if report.kelas and report.kelas.strip()
            }
        )
        return kelas_values


sheets_logger = GoogleSheetsLogger()


def validate_tanggal(tanggal: str) -> str:
    try:
        parsed = datetime.strptime(tanggal, "%d-%m-%Y")
    except ValueError as error:
        raise ValueError(
            "Format tanggal harus `dd-mm-yyyy`, contoh: `26-08-2026`."
        ) from error

    if parsed.year < 2020 or parsed.year > 2100:
        raise ValueError(
            "Tahun pada tanggal terlihat tidak wajar. Gunakan format `dd-mm-yyyy`, contoh: `26-08-2026`."
        )

    return parsed.strftime("%d-%m-%Y")


def build_formal_summary(report: ReportRow) -> str:
    return (
        f"Pada tanggal {report.tanggal}, kegiatan pembelajaran untuk kelas/kelompok "
        f"{report.kelas} dilaksanakan dengan materi *{report.materi}* selama {report.durasi} "
        f"dengan jumlah peserta hadir {report.jumlah_hadir}."
    )


def build_report_message(report: ReportRow, author_mention: str) -> str:
    return (
        "## LAPORAN KEGIATAN PEMBELAJARAN\n\n"
        f"**Tanggal:** {report.tanggal}\n"
        f"**Kelas/Kelompok:** {report.kelas}\n"
        f"**Materi:** {report.materi}\n"
        f"**Durasi:** {report.durasi}\n"
        f"**Jumlah Peserta Hadir:** {report.jumlah_hadir}\n\n"
        f"**Ringkasan Formal:**\n{build_formal_summary(report)}\n\n"
        f"**Aktivitas Utama:**\n{report.aktivitas}\n\n"
        f"**Hasil/Capaian:**\n{report.hasil}\n\n"
        f"**Kendala:**\n{report.kendala}\n\n"
        f"**Tindak Lanjut:**\n{report.tindak_lanjut}\n\n"
        f"*Dikirim oleh:* {author_mention}"
    )


def format_report_brief(report: ReportRow) -> str:
    return (
        f"- {report.tanggal} | {report.kelas} | {report.materi} | "
        f"Hadir: {report.jumlah_hadir}"
    )


def filter_reports_by_date(
    reports: list[ReportRow],
    start_date: datetime,
    end_date: datetime,
) -> list[ReportRow]:
    return [
        report
        for report in reports
        if start_date <= report.parsed_date <= end_date
    ]


def build_rekap_text(title: str, reports: list[ReportRow]) -> str:
    if not reports:
        return f"## {title}\n\nBelum ada data laporan pada periode tersebut."

    kelas_unik = sorted({report.kelas for report in reports if report.kelas})
    materi_unik = sorted({report.materi for report in reports if report.materi})

    lines = [
        f"## {title}",
        "",
        f"**Jumlah Laporan:** {len(reports)}",
        f"**Kelas/Kelompok Terlibat:** {', '.join(kelas_unik) if kelas_unik else '-'}",
        f"**Materi yang Dibahas:** {', '.join(materi_unik) if materi_unik else '-'}",
        "",
        "**Daftar Laporan:**",
    ]
    lines.extend(format_report_brief(report) for report in reports)
    return "\n".join(lines)


def generate_pdf_bytes(title: str, subtitle: str, reports: list[ReportRow]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles["Title"]),
        Spacer(1, 0.3 * cm),
        Paragraph(subtitle, styles["Normal"]),
        Spacer(1, 0.5 * cm),
    ]

    if not reports:
        story.append(Paragraph("Belum ada data laporan pada periode tersebut.", styles["Normal"]))
    else:
        table_data = [[
            "Tanggal",
            "Kelas",
            "Materi",
            "Durasi",
            "Jumlah Hadir",
            "Hasil/Capaian",
        ]]
        for report in reports:
            table_data.append([
                report.tanggal,
                report.kelas,
                report.materi,
                report.durasi,
                report.jumlah_hadir,
                report.hasil,
            ])

        table = Table(
            table_data,
            colWidths=[2.2 * cm, 2.2 * cm, 4.0 * cm, 2.5 * cm, 2.6 * cm, 6.0 * cm],
            repeatRows=1,
        )
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f4f4f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ])
        )
        story.append(table)

    doc.build(story)
    return buffer.getvalue()


async def kelas_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    suggestions = []
    try:
        suggestions = sheets_logger.get_unique_kelas()
    except Exception as error:
        logger.warning("Gagal mengambil autocomplete kelas dari Google Sheets: %s", error)

    normalized_current = current.lower().strip()
    if normalized_current:
        suggestions = [
            item for item in suggestions if normalized_current in item.lower()
        ]

    suggestions = suggestions[:MAX_AUTOCOMPLETE_CHOICES]
    return [app_commands.Choice(name=item, value=item) for item in suggestions]


class LearningReportModal(discord.ui.Modal, title="Form Laporan Pembelajaran"):
    aktivitas = discord.ui.TextInput(
        label="Aktivitas Utama",
        style=discord.TextStyle.paragraph,
        placeholder="Contoh: penyampaian materi, diskusi, praktik, tanya jawab",
        required=True,
        max_length=1000,
    )
    hasil = discord.ui.TextInput(
        label="Hasil / Capaian",
        style=discord.TextStyle.paragraph,
        placeholder="Contoh: siswa memahami struktur HTML dasar",
        required=True,
        max_length=1000,
    )
    kendala = discord.ui.TextInput(
        label="Kendala",
        style=discord.TextStyle.paragraph,
        placeholder="Contoh: beberapa siswa masih bingung pada bagian tertentu",
        required=True,
        max_length=1000,
    )
    tindak_lanjut = discord.ui.TextInput(
        label="Tindak Lanjut",
        style=discord.TextStyle.paragraph,
        placeholder="Contoh: review materi dan latihan tambahan pertemuan berikutnya",
        required=True,
        max_length=1000,
    )

    def __init__(self, header: ReportHeader):
        super().__init__()
        self.header = header

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Laporan hanya bisa dikirim dari server Discord.",
                ephemeral=True,
            )
            return

        channel = discord.utils.get(interaction.guild.text_channels, name=REPORT_CHANNEL_NAME)
        if channel is None:
            await interaction.response.send_message(
                (
                    f"Channel `#{REPORT_CHANNEL_NAME}` tidak ditemukan. "
                    "Buat channel tersebut atau ubah nama channel di file konfigurasi."
                ),
                ephemeral=True,
            )
            return

        report = ReportRow(
            tanggal=self.header.tanggal,
            kelas=self.header.kelas,
            materi=self.header.materi,
            durasi=self.header.durasi,
            jumlah_hadir=self.header.jumlah_hadir,
            aktivitas=str(self.aktivitas).strip(),
            hasil=str(self.hasil).strip(),
            kendala=str(self.kendala).strip(),
            tindak_lanjut=str(self.tindak_lanjut).strip(),
            dikirim_oleh=str(interaction.user),
            server_discord=interaction.guild.name,
        )

        await channel.send(build_report_message(report, interaction.user.mention))

        saved_to_sheets = False
        sheets_error: Optional[str] = None
        try:
            saved_to_sheets = sheets_logger.append_report(report)
        except Exception as error:
            logger.exception("Gagal menyimpan laporan ke Google Sheets", exc_info=error)
            sheets_error = str(error)

        success_message = f"Laporan berhasil dikirim ke channel {channel.mention}."
        if saved_to_sheets:
            success_message += " Data juga berhasil disimpan ke Google Sheets."
        elif sheets_error:
            success_message += (
                " Namun penyimpanan ke Google Sheets gagal. "
                f"Detail singkat: `{sheets_error}`"
            )
        else:
            success_message += " Google Sheets belum aktif karena konfigurasi belum diisi."

        await interaction.response.send_message(success_message, ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        logger.exception("Gagal memproses modal laporan", exc_info=error)
        message = "Terjadi error saat memproses laporan. Cek log bot untuk detail."
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info("Bot login sebagai %s", bot.user)
    if sheets_logger.enabled:
        logger.info(
            "Google Sheets aktif jika token OAuth tersedia. Spreadsheet ID: %s | Worksheet: %s",
            GOOGLE_SHEETS_SPREADSHEET_ID,
            GOOGLE_SHEETS_WORKSHEET_NAME,
        )
    else:
        logger.info("Google Sheets belum aktif. Bot tetap berjalan tanpa penyimpanan Sheets.")

    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            logger.info("Slash command tersinkron ke guild %s: %s command", GUILD_ID, len(synced))
        else:
            synced = await bot.tree.sync()
            logger.info("Slash command global tersinkron: %s command", len(synced))
    except Exception:
        logger.exception("Gagal sync slash command")


@bot.tree.command(
    name="lapor",
    description="Buat laporan kegiatan pembelajaran dengan format tetap",
)
@app_commands.describe(
    tanggal="Tanggal pembelajaran, contoh: 26-08-2026",
    kelas="Nama kelas atau kelompok",
    materi="Materi yang diajarkan",
    durasi="Durasi kegiatan, contoh: 90 menit",
    jumlah_hadir="Jumlah peserta yang hadir, contoh: 28 siswa",
)
@app_commands.autocomplete(kelas=kelas_autocomplete)
async def lapor(
    interaction: discord.Interaction,
    tanggal: str,
    kelas: str,
    materi: str,
    durasi: str,
    jumlah_hadir: str,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "Command ini hanya bisa digunakan di dalam server Discord.",
            ephemeral=True,
        )
        return

    try:
        tanggal = validate_tanggal(tanggal.strip())
    except ValueError as error:
        await interaction.response.send_message(str(error), ephemeral=True)
        return

    header = ReportHeader(
        tanggal=tanggal,
        kelas=kelas.strip(),
        materi=materi.strip(),
        durasi=durasi.strip(),
        jumlah_hadir=jumlah_hadir.strip(),
    )
    await interaction.response.send_modal(LearningReportModal(header))


@bot.tree.command(
    name="rekap_mingguan",
    description="Lihat rekap laporan mingguan berdasarkan rentang tanggal",
)
@app_commands.describe(
    mulai="Tanggal mulai, format dd-mm-yyyy",
    akhir="Tanggal akhir, format dd-mm-yyyy",
)
async def rekap_mingguan(
    interaction: discord.Interaction,
    mulai: str,
    akhir: str,
) -> None:
    await interaction.response.defer(ephemeral=True)

    try:
        start_date = datetime.strptime(validate_tanggal(mulai.strip()), "%d-%m-%Y")
        end_date = datetime.strptime(validate_tanggal(akhir.strip()), "%d-%m-%Y")
    except ValueError as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return

    if start_date > end_date:
        await interaction.followup.send(
            "Tanggal mulai tidak boleh lebih besar dari tanggal akhir.",
            ephemeral=True,
        )
        return

    try:
        reports = filter_reports_by_date(sheets_logger.read_reports(), start_date, end_date)
    except Exception as error:
        await interaction.followup.send(
            f"Gagal membaca data Google Sheets: `{error}`",
            ephemeral=True,
        )
        return

    title = f"REKAP MINGGUAN {start_date.strftime('%d-%m-%Y')} s.d. {end_date.strftime('%d-%m-%Y')}"
    await interaction.followup.send(build_rekap_text(title, reports), ephemeral=True)


@bot.tree.command(
    name="rekap_bulanan",
    description="Lihat rekap laporan bulanan",
)
@app_commands.describe(
    bulan="Nomor bulan 1-12",
    tahun="Tahun, contoh 2026",
)
async def rekap_bulanan(
    interaction: discord.Interaction,
    bulan: app_commands.Range[int, 1, 12],
    tahun: app_commands.Range[int, 2020, 2100],
) -> None:
    await interaction.response.defer(ephemeral=True)

    start_date = datetime(tahun, bulan, 1)
    if bulan == 12:
        end_date = datetime(tahun + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(tahun, bulan + 1, 1) - timedelta(days=1)

    try:
        reports = filter_reports_by_date(sheets_logger.read_reports(), start_date, end_date)
    except Exception as error:
        await interaction.followup.send(
            f"Gagal membaca data Google Sheets: `{error}`",
            ephemeral=True,
        )
        return

    title = f"REKAP BULANAN {start_date.strftime('%B %Y').upper()}"
    await interaction.followup.send(build_rekap_text(title, reports), ephemeral=True)


@bot.tree.command(
    name="export_pdf",
    description="Export laporan pada rentang tanggal menjadi PDF",
)
@app_commands.describe(
    mulai="Tanggal mulai, format dd-mm-yyyy",
    akhir="Tanggal akhir, format dd-mm-yyyy",
    judul="Judul PDF opsional",
)
async def export_pdf(
    interaction: discord.Interaction,
    mulai: str,
    akhir: str,
    judul: Optional[str] = None,
) -> None:
    await interaction.response.defer(ephemeral=True)

    try:
        start_date = datetime.strptime(validate_tanggal(mulai.strip()), "%d-%m-%Y")
        end_date = datetime.strptime(validate_tanggal(akhir.strip()), "%d-%m-%Y")
    except ValueError as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return

    if start_date > end_date:
        await interaction.followup.send(
            "Tanggal mulai tidak boleh lebih besar dari tanggal akhir.",
            ephemeral=True,
        )
        return

    try:
        reports = filter_reports_by_date(sheets_logger.read_reports(), start_date, end_date)
    except Exception as error:
        await interaction.followup.send(
            f"Gagal membaca data Google Sheets: `{error}`",
            ephemeral=True,
        )
        return

    title = judul.strip() if judul and judul.strip() else "Laporan Pembelajaran"
    subtitle = f"Periode {start_date.strftime('%d-%m-%Y')} s.d. {end_date.strftime('%d-%m-%Y')}"
    pdf_bytes = generate_pdf_bytes(title, subtitle, reports)
    filename = (
        f"laporan_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
    )

    discord_file = discord.File(io.BytesIO(pdf_bytes), filename=filename)
    await interaction.followup.send(
        content=f"PDF berhasil dibuat untuk periode {subtitle}.",
        file=discord_file,
        ephemeral=True,
    )


if __name__ == "__main__":
    bot.run(TOKEN)
