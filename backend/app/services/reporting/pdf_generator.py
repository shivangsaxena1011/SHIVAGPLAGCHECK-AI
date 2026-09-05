"""Professional Academic PDF Report Generator.

Complies strictly with Section 17 PDF Report requirements:
- Page 1: Cover page with title, submission information, and score summary cards
  (Similarity %, AI likelihood %, Sources found, Word & page count).
- Page 2: Similarity breakdown (Exact, Near-exact, Semantic) and Source-by-source distribution table.
- Page 3+: Highlighted document text with page markings.
- Final Section: Methodology & Disclaimers.
"""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)


class PDFReportGenerator:
    """Generates professional academic originality reports in PDF format."""

    def generate_file(
        self,
        output_path: Path,
        submission: any,
        document: any,
        breakdown: any,
        sources: list,
        ai_result: any,
        references: list,
        matches: list,
    ) -> None:
        """Render and save PDF report to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e3a8a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#4b5563"),
        )
        section_heading = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1f2937"),
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerText",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#6b7280"),
        )

        story = []

        # ==========================================
        # PAGE 1: COVER & SCORE SUMMARY
        # ==========================================
        story.append(Paragraph("SHIVANG PLAGCHECK AI", title_style))
        story.append(Paragraph("Academic Similarity, AI-Writing & Citation Integrity Platform", subtitle_style))
        story.append(Spacer(1, 15))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceAfter=15))

        # Submission Information Table
        sub_info_data = [
            [Paragraph("<b>Document Title:</b>", body_style), Paragraph(str(submission.title), body_style)],
            [Paragraph("<b>File Name:</b>", body_style), Paragraph(str(submission.original_filename), body_style)],
            [Paragraph("<b>Analysis Date:</b>", body_style), Paragraph(submission.created_at.strftime("%Y-%m-%d %H:%M UTC"), body_style)],
            [Paragraph("<b>Word Count:</b>", body_style), Paragraph(f"{document.word_count:,}", body_style)],
            [Paragraph("<b>Character Count:</b>", body_style), Paragraph(f"{document.char_count:,}", body_style)],
            [Paragraph("<b>Total Pages:</b>", body_style), Paragraph(str(document.page_count), body_style)],
        ]
        sub_table = Table(sub_info_data, colWidths=[140, 380])
        sub_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(sub_table)
        story.append(Spacer(1, 25))

        # Top-level score summary cards table
        card_style_val = ParagraphStyle("CardVal", parent=styles["Normal"], fontSize=24, leading=28, fontName="Helvetica-Bold", alignment=1)
        card_style_lbl = ParagraphStyle("CardLbl", parent=styles["Normal"], fontSize=9, leading=12, textColor=colors.HexColor("#4b5563"), alignment=1)

        sim_cell = [
            Paragraph(f"<font color='#dc2626'>{breakdown.overall_similarity}%</font>", card_style_val),
            Paragraph("SIMILARITY INDEX", card_style_lbl),
        ]
        ai_cell = [
            Paragraph(f"<font color='#d97706'>{ai_result.overall_likelihood}%</font>", card_style_val),
            Paragraph("EST. AI LIKELIHOOD", card_style_lbl),
        ]
        src_cell = [
            Paragraph(f"<font color='#2563eb'>{len(sources)}</font>", card_style_val),
            Paragraph("SOURCES FOUND", card_style_lbl),
        ]

        scores_table = Table([[sim_cell, ai_cell, src_cell]], colWidths=[173, 173, 174])
        scores_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 15),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ])
        )
        story.append(scores_table)
        story.append(Spacer(1, 25))

        # Quick Highlights Overview
        story.append(Paragraph("<b>Similarity Breakdown:</b>", section_heading))
        breakdown_data = [
            [Paragraph("Exact Copying", body_style), Paragraph(f"{breakdown.exact_similarity}%", body_style)],
            [Paragraph("Near-Verbatim Alignment", body_style), Paragraph(f"{breakdown.near_exact_similarity}%", body_style)],
            [Paragraph("Semantic / Paraphrase Similarity", body_style), Paragraph(f"{breakdown.semantic_similarity}%", body_style)],
            [Paragraph("Excluded Direct Quotations", body_style), Paragraph(f"{breakdown.excluded_quote_words} words", body_style)],
            [Paragraph("Excluded Bibliography", body_style), Paragraph(f"{breakdown.excluded_bibliography_words} words", body_style)],
        ]
        breakdown_table = Table(breakdown_data, colWidths=[300, 220])
        breakdown_table.setStyle(
            TableStyle([
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(breakdown_table)

        story.append(PageBreak())

        # ==========================================
        # PAGE 2: SOURCE-BY-SOURCE ANALYSIS
        # ==========================================
        story.append(Paragraph("Identified Sources & Contribution Breakdown", section_heading))
        story.append(Spacer(1, 8))

        if sources:
            src_table_data = [
                [
                    Paragraph("<b>#</b>", body_style),
                    Paragraph("<b>Source Title & Metadata</b>", body_style),
                    Paragraph("<b>Match Type</b>", body_style),
                    Paragraph("<b>Contrib.</b>", body_style),
                ]
            ]
            for idx, s in enumerate(sources[:20], 1):
                author_str = f" ({s.authors})" if s.authors else ""
                url_str = f"<br/><font color='#2563eb'>{s.url[:45]}...</font>" if s.url else ""
                title_meta = f"<b>{s.title}</b>{author_str}{url_str}"
                src_table_data.append([
                    Paragraph(str(idx), body_style),
                    Paragraph(title_meta, body_style),
                    Paragraph(s.primary_match_type, body_style),
                    Paragraph(f"<b>{s.similarity_contribution}%</b>", body_style),
                ])

            src_table = Table(src_table_data, colWidths=[25, 340, 95, 60])
            src_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(src_table)
        else:
            story.append(Paragraph("No significant matching sources found in comparison databases.", body_style))

        story.append(PageBreak())

        # ==========================================
        # PAGE 3+: DOCUMENT HIGHLIGHTS
        # ==========================================
        story.append(Paragraph("Annotated Document & Page Matches", section_heading))
        story.append(Spacer(1, 8))

        for page in document.pages[:15]:  # Render up to 15 pages in PDF report
            story.append(Paragraph(f"<b>--- PAGE {page.page_number} ---</b>", ParagraphStyle("PageHead", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#64748b"), fontName="Helvetica-Bold")))
            story.append(Spacer(1, 4))
            
            # Simple text escaping and paragraph formatting
            escaped_text = page.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(escaped_text, body_style))
            story.append(Spacer(1, 14))

        # ==========================================
        # FINAL: METHODOLOGY & DISCLAIMER
        # ==========================================
        story.append(Spacer(1, 20))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=10))
        story.append(Paragraph("<b>Methodology & Academic Disclaimers:</b>", ParagraphStyle("DiscHead", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", textColor=colors.HexColor("#475569"))))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            "1. <b>Similarity Score</b> indicates the mathematical proportion of analyzed text that overlaps with identified comparison sources. Human academic evaluation is required to determine whether a match constitutes plagiarism, fair use, or appropriate scholarly citation.<br/>"
            "2. <b>AI Writing Likelihood</b> is an automated statistical estimate based on stylometric variance, burstiness, transition phrase density, and syntactical uniformity. It must not be considered definitive proof of AI authorship.<br/>"
            "3. <b>Exclusions</b>: Direct quotations within quotation marks, bibliographies, and short phrase fragments below the threshold were excluded per institutional policy.",
            disclaimer_style,
        ))

        doc.build(story)
