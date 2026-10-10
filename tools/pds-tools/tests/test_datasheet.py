"""Datasheet reading: timing pages, tables as printed, search, page text."""

from pds_tools import datasheet


def write_pdf(path, pages):
    """A minimal PDF with one text line per entry of each page (Helvetica), enough for the text layer."""
    objects = ["<< /Type /Catalog /Pages 2 0 R >>", None, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    kids = []
    for lines in pages:
        stream = "BT /F1 10 Tf 50 800 Td 14 TL " + " ".join(
            "(" + line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ") Tj T*" for line in lines) + " ET"
        objects.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {len(objects)} 0 R "
                       "/Resources << /Font << /F1 3 0 R >> >> >>")
        kids.append(f"{len(objects)} 0 R")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>"
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(out)


def sample(tmp_path):
    pdf = tmp_path / "adc.pdf"
    write_pdf(pdf, [
        ["XYZ1234 12-bit ADC with SPI interface", "Features", "Low power, 8 channels"],
        ["1 Features ........ 1", "2 Pin description ........ 3", "6.6 Timing Requirements ........ 6", "7 Layout ........ 9",
         "8 Ordering ........ 10"],
        ["6.6 Timing Requirements", "PARAMETER MIN MAX UNIT", "tSCK SCK period 25 ns", "tSUDI SDI setup time before SCK 4 ns",
         "tHDI SDI hold time after SCK 1 ns", "tDO SCK to SDO valid 12 ns", "(1) Measured with CL = 25 pF",
         "Figure 3. SPI Timing Diagram"],
        ["Typical application", "Connect the reference to the input through the buffer."],
    ])
    return str(pdf)


def test_open_finds_timing_page(tmp_path):
    info = datasheet.open_datasheet(sample(tmp_path))
    assert info["text"] and info["pages"] == 4
    pages = {p["page"]: p for p in info["timing_pages"]}
    assert 3 in pages and 2 not in pages  # the table of contents does not count
    assert "6.6 Timing Requirements" in pages[3]["headings"]
    assert pages[3]["figures"] == ["Figure 3. SPI Timing Diagram"]


def test_timing_lines_search_and_page(tmp_path):
    path = sample(tmp_path)
    result = datasheet.timing_tables(path, [3])
    page = result["pages"][0]
    assert page["tables"] == []  # no ruled table: the page text instead, no row lost
    assert "tSUDI SDI setup time before SCK 4 ns" in page["text"]
    assert page["notes"] == ["(1) Measured with CL = 25 pF"]
    hits = datasheet.search(path, "t SUDI")["hits"]
    assert hits and hits[0]["page"] == 3
    assert datasheet.search(path, "th")["hits"] == []  # a short symbol is a whole word: not "the", "through"
    assert [h["page"] for h in datasheet.search(path, "tDO")["hits"]] == [3]
    assert "SCK to SDO valid" in datasheet.page_text(path, 3)["text"]


def test_table_as_printed():
    # Rows as pdfplumber extracts them from the SN74HC595 switching characteristics (subscripts on their own line,
    # merged cells as None, a cell spanning the TYP and MAX columns)
    raw = [["PARAMETER", "FROM\n(INPUT)", "LOAD", "V", "T = 25°C", None, None, "SN74HC595", None, "UNIT"],
           ["", "", "CAPACITANCE", "CC", "MIN", "TYP", "MAX", "MIN", "MAX", ""],
           ["t\npd", "SRCLK", "50 pF", "2 V", "50 160", None, None, "", "200", "ns"],
           [None, None, None, "4.5 V", "17 32", None, None, "", "40", None],
           ["t Set-up time\nsu", "SER", "", "4.5 V", "20", None, None, "25", None, "ns"]]
    table = datasheet._table(raw)
    assert table["columns"][:2] == ["PARAMETER", "FROM (INPUT)"]
    assert table["columns"][4:9] == ["T = 25°C MIN", "T = 25°C TYP", "T = 25°C MAX", "SN74HC595 MIN", "SN74HC595 MAX"]
    assert table["rows"][1][:4] == ["tpd", "SRCLK", "50 pF", "4.5 V"]  # merged cells filled down
    assert table["rows"][2][0] == "tsu Set-up time"
    assert "merged_values" in table


def test_no_text_layer(tmp_path):
    pdf = tmp_path / "scan.pdf"
    write_pdf(pdf, [[]])
    info = datasheet.open_datasheet(str(pdf))
    assert info["text"] is False and "scanned" in info["message"]


def test_layout_keeps_columns(tmp_path):
    path = sample(tmp_path)
    page = datasheet.page_text(path, 3, layout=True)
    assert page["layout"] and "tSUDI SDI setup time before SCK 4 ns" in " ".join(page["text"].split())


def test_board_device_notes():
    listing = datasheet.board_devices()
    assert {"sdram", "adc-ltc2308", "adc-ad7928", "level-shifter-txb0104", "vga-adv7123", "audio-wm8731", "video-adv7180"} <= set(listing["devices"])
    assert "never" in listing["rule"].lower() or "nothing here may be used" in listing["rule"].lower()
    ltc = datasheet.board_devices("ltc2308")
    assert ltc["device"] == "adc-ltc2308" and "OVDD = 5 V" in ltc["notes"]
    sdram = datasheet.board_devices("sdram")["notes"]
    assert "Not named" in sdram or "not named" in sdram
    missing = datasheet.board_devices("74hc595")
    assert missing["ok"] is False and "the student provides it" in missing["message"]
