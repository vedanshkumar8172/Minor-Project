# ── Advanced Date Patterns (Covers MFG, PKD, Batch dates, and Standalone dates) ──
    _DATE_BODY = (
        r'(?:'
        r'[0-9]{1,2}[\/\.\-][0-9]{1,2}[\/\.\-][0-9]{2,4}'    # DD/MM/YYYY or DD-MM-YY
        r'|[0-9]{1,2}\s+[a-zA-Z]{3,9}\.?\s+[0-9]{2,4}'       # 15 Jun 2025 / 15 June 2025
        r'|[a-zA-Z]{3,9}\.?\s*[0-9]{4}'                       # Jun 2025
        r'|[0-9]{4}[\/\.\-][0-9]{1,2}(?:[\/\.\-][0-9]{1,2})?' # 2025/06/15
        r'|[0-9]{1,2}[\/\.\-][0-9]{4}'                        # 06/2025
        r')'
    )
    _D = r'(?:\s*(?:date|dt|on|by)?\s*)?[:\-\.]?\s*'

    mfg_date = _first_match([
        rf'(?:mfd|mfg|manufactur(?:ed|ing)|pkd|packed|pkg)(?:\s*(?:date|dt)?){_D}({_DATE_BODY})',
        rf'(?:mfd|mfg|pkd)\s*[:\-\.]\s*({_DATE_BODY})',
        rf'(?:date\s+of\s+(?:manufacture|mfg|packing|pkd))\s*[:\-\.]?\s*({_DATE_BODY})',
        # Fallback to search any standalone date format if labels are missing
        rf'\b({_DATE_BODY})\b',
    ], raw_text)

    pack_date = _first_match([
        rf'(?:pack(?:ed|ing|aged|aging)?|pkd)(?:\s*(?:date|dt)?){_D}({_DATE_BODY})',
        rf'(?:date\s+of\s+pack(?:aging)?)\s*[:\-\.]?\s*({_DATE_BODY})',
    ], raw_text)
    
    # Intelligent Fallback
    if not pack_date and mfg_date:
        pack_date = mfg_date
    elif not mfg_date and pack_date:
        mfg_date = pack_date
