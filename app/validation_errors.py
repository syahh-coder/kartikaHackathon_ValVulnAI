"""Safe form feedback. Never return Pydantic input, context, raw messages or unknown field names."""
from fastapi.exceptions import RequestValidationError

LABELS = {"source_text": "Teks guideline", "in_scope_rules": "Aturan in-scope",
          "out_of_scope_rules": "Aturan out-of-scope", "asset_alias": "Alias aset",
          "path_template": "Pola path", "methods": "Metode HTTP", "capabilities": "Kategori kemampuan",
          "business_rules": "Aturan bisnis", "business_rules_version": "Versi aturan bisnis",
          "login_name": "Username", "password": "Password", "body": "Isi permintaan"}


def safe_field_errors(exc: RequestValidationError) -> list[dict[str, str]]:
    fields = []
    for error in exc.errors()[:8]:
        location = error.get("loc", ())
        parts = [p for p in location if p != "body"]
        known = bool(parts) and all((type(p) is int and 0 <= p < 100) or
                                   (isinstance(p, str) and p in LABELS) for p in parts)
        label = " · ".join(str(p+1) if type(p) is int else LABELS[p] for p in parts) if known else "Isi permintaan"
        path = ".".join(str(p) for p in parts) if known else "body"
        kind = error.get("type")
        if kind == "missing":
            message = "wajib diisi."
        elif kind == "string_too_short":
            message = "belum diisi atau terlalu pendek."
        elif kind == "string_too_long":
            message = "teks terlalu panjang."
        elif kind == "too_short":
            message = "tambahkan setidaknya satu item."
        elif kind == "too_long":
            message = "jumlah item melampaui batas."
        elif kind == "extra_forbidden":
            message = "ada field tambahan yang tidak diterima."
        elif kind == "json_invalid":
            message = "JSON tidak sah; periksa tanda kutip, kurung dan koma."
        elif kind in {"list_type", "string_type", "dict_type", "model_attributes_type"}:
            message = "jenis data tidak sesuai format formulir."
        elif kind == "literal_error" and "methods" in parts:
            message = "gunakan GET, POST, PUT, PATCH atau DELETE sesuai profil program."
        elif kind == "literal_error" and "capabilities" in parts:
            message = "gunakan kategori BAC, XSS, UPLOAD atau BUSINESS_LOGIC sesuai profil program."
        elif "source_text" in parts:
            message = "isi teks guideline yang menjelaskan scope program."
        elif "login_name" in parts:
            message = "gunakan huruf kecil, angka, titik, garis bawah atau tanda minus tanpa spasi."
        else:
            message = "nilai atau format belum sesuai persyaratan."
        fields.append({"field": path, "message": f"{label}: {message}"})
    return fields
