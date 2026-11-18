# 00a - Terjemahan deskripsi tool MCP (EN -> ID) yang sudah divalidasi, disimpan sebagai JSON.
# Dipakai oleh kernel mcp-dataset-build untuk merakit tools_id.json.

import json

# ---------------------------------------------------------------------------
# 1. Terjemahan deskripsi. Kunci: "tool|param" ("tool|" = deskripsi tool).
#    Nama tool, nama parameter, nilai contoh, dan token kode tidak diterjemahkan.
# ---------------------------------------------------------------------------
P = "Path absolut, atau relatif terhadap direktori yang diizinkan; path harus mengarah ke lokasi di dalam direktori yang diizinkan."
ONLY = "Hanya berfungsi di dalam direktori yang diizinkan."
EXCL = ("Pola untuk entri yang akan dikecualikan beserta isinya, dicocokkan dengan path setiap entri relatif terhadap path. "
        "Pola tanpa '*' cocok dengan nama tersebut di kedalaman mana pun ('node_modules' mengecualikan setiap direktori "
        "node_modules); pola dengan '*' adalah glob yang dicocokkan apa adanya, dan pola yang diakhiri '/**' juga "
        "mengecualikan direktori yang disebutkannya.")
OBSLIM = ("Kembalikan paling banyak sejumlah ini observasi per entitas (yang pertama, sesuai urutan penambahannya) dan "
          "tambahkan total observasi setiap entitas sebagai observationCount. Gunakan 0 untuk nama, tipe, dan jumlah saja: "
          "gambaran ringkas yang murah untuk graf yang besar, setelah itu open_nodes dapat membaca secara lengkap entitas "
          "yang Anda perlukan. Kosongkan untuk mengembalikan semua observasi.")
TS_EX = ("Menerima: format ISO 8601 (misalnya, '2024-01-15T14:30:25'), tanggal relatif (misalnya, '2 weeks ago', "
         "'yesterday'), atau tanggal absolut (misalnya, '2024-01-15', 'Jan 15 2024')")
TZ_OPT = "Opsional: jika dikosongkan, bawaannya adalah zona waktu lokal server, 'Asia/Jakarta'."
TZ = f"Nama zona waktu IANA (misalnya, 'America/New_York', 'Europe/London'). {TZ_OPT}"

ID = {
    # ---- filesystem ----
    "read_file|": "Membaca seluruh isi file sebagai teks. USANG: Gunakan read_text_file sebagai gantinya.",
    "read_file|path": f"File yang akan dibaca sebagai teks. {P}",
    "read_file|tail": "Jika diberikan, hanya mengembalikan N baris terakhir dari file",
    "read_file|head": "Jika diberikan, hanya mengembalikan N baris pertama dari file",
    "read_text_file|": (
        "Membaca seluruh isi file dari sistem file sebagai teks. Menangani berbagai encoding teks dan memberikan pesan "
        "galat yang terperinci jika file tidak dapat dibaca. Gunakan tool ini ketika Anda perlu memeriksa isi satu file. "
        "Gunakan parameter 'head' untuk membaca hanya N baris pertama dari file, atau parameter 'tail' untuk membaca hanya "
        f"N baris terakhir dari file. Memproses file sebagai teks apa pun ekstensinya. {ONLY}"),
    "read_text_file|path": f"File yang akan dibaca sebagai teks. {P}",
    "read_text_file|tail": "Jika diberikan, hanya mengembalikan N baris terakhir dari file",
    "read_text_file|head": "Jika diberikan, hanya mengembalikan N baris pertama dari file",
    "read_media_file|": (
        "Membaca file dan mengembalikannya sebagai blok konten berenkode base64 beserta tipe MIME-nya. File gambar dan "
        "audio dikembalikan sebagai konten gambar/audio; jenis file lainnya dikembalikan sebagai resource tersemat. "
        f"{ONLY}"),
    "read_media_file|path": f"File gambar, audio, atau file lain yang akan dibaca sebagai base64. {P}",
    "read_multiple_files|": (
        "Membaca isi beberapa file sekaligus. Cara ini lebih efisien daripada membaca file satu per satu ketika Anda perlu "
        "menganalisis atau membandingkan beberapa file. Isi setiap file dikembalikan bersama path-nya sebagai acuan. "
        f"Kegagalan membaca satu file tidak akan menghentikan seluruh operasi. {ONLY}"),
    "read_multiple_files|paths": (
        "Array berisi path file yang akan dibaca. Setiap path harus berupa string yang mengarah ke file yang valid di "
        "dalam direktori yang diizinkan."),
    "write_file|": (
        "Membuat file baru atau menimpa seluruh isi file yang sudah ada dengan konten baru. Gunakan dengan hati-hati karena "
        "tool ini akan menimpa file yang sudah ada tanpa peringatan. Menangani konten teks dengan encoding yang tepat. "
        f"{ONLY}"),
    "write_file|path": f"File yang akan dibuat, atau ditimpa jika sudah ada; direktori induknya harus sudah ada. {P}",
    "write_file|content": "Seluruh teks yang akan menjadi isi file, menggantikan isi sebelumnya",
    "append_file|": (
        "Menambahkan teks ke akhir file, dan membuat file tersebut jika belum ada. Isi yang sudah ada tidak pernah diubah "
        "atau diganti. Teks ditambahkan persis seperti yang diberikan, tanpa tambahan baris baru sebelum atau sesudahnya, "
        f"jadi akhiri teks dengan baris baru jika penambahan berikutnya harus dimulai di baris baru. {ONLY}"),
    "append_file|path": f"File yang akan ditambahi teks; file akan dibuat jika belum ada. {P}",
    "append_file|content": (
        "Teks yang akan ditambahkan, persis seperti yang diberikan. Tidak ada baris baru yang ditambahkan: akhiri dengan "
        "\\n jika penambahan berikutnya harus dimulai di baris baru."),
    "edit_file|": (
        "Melakukan pengeditan berbasis baris pada file teks. Pengeditan diterapkan secara berurutan, masing-masing pada "
        "hasil pengeditan sebelumnya, dan masing-masing mengganti kecocokan pertama dari oldText dengan newText. oldText "
        "harus sama persis dengan teks di file, kecuali bahwa akhir baris (LF atau CRLF) tidak pernah berpengaruh dan, jika "
        "tidak ada kecocokan persis, rangkaian baris utuh dianggap cocok jika setiap barisnya sama setelah spasi di awal "
        "dan akhir baris diabaikan (newText kemudian mengikuti indentasi file). Spasi di dalam baris harus sama. Jika ada "
        "pengeditan yang tidak menemukan kecocokan, tidak ada yang ditulis dan pesan galat menampilkan baris-baris file "
        "yang paling mirip, lengkap dengan nomornya, untuk disalin menjadi oldText. Mengembalikan diff bergaya git yang "
        f"menunjukkan perubahan yang dibuat. {ONLY}"),
    "edit_file|path": f"File teks yang akan diedit. {P}",
    "edit_file|edits": (
        "Penggantian yang akan dilakukan, diterapkan secara berurutan, masing-masing pada hasil penggantian sebelumnya. "
        "Jika ada satu saja yang tidak menemukan kecocokan, tidak ada yang ditulis."),
    "edit_file|dryRun": "Pratinjau perubahan menggunakan format diff bergaya git",
    "create_directory|": (
        "Membuat direktori baru atau memastikan sebuah direktori ada. Dapat membuat beberapa direktori bertingkat dalam "
        "satu operasi. Jika direktori sudah ada, operasi ini akan berhasil tanpa pemberitahuan. Sangat cocok untuk "
        f"menyiapkan struktur direktori proyek atau memastikan path yang diperlukan tersedia. {ONLY}"),
    "create_directory|path": (
        "Direktori yang akan dibuat, beserta direktori induk yang belum ada; direktori yang sudah ada dibiarkan apa "
        f"adanya. {P}"),
    "list_directory|": (
        "Menampilkan daftar file dan direktori yang berada langsung di dalam sebuah path, masing-masing ditandai [FILE] "
        "atau [DIR]. Gunakan untuk melihat isi sebuah direktori; jika Anda juga memerlukan ukuran setiap entri atau ingin "
        "entri diurutkan berdasarkan ukuran, gunakan list_directory_with_sizes, dan untuk tampilan rekursif gunakan "
        f"directory_tree. Mengembalikan satu baris per entri. {ONLY}"),
    "list_directory|path": f"Direktori yang akan ditampilkan isinya. {P}",
    "list_directory_with_sizes|": (
        "Menampilkan daftar file dan direktori yang berada langsung di dalam sebuah path beserta ukuran setiap file, "
        "ditandai [FILE] atau [DIR], diurutkan berdasarkan nama atau berdasarkan ukuran dari yang terbesar (sortBy). "
        "Gunakan ketika ukuran penting, misalnya untuk mencari file terbesar; untuk nama saja, gunakan list_directory, "
        f"yang mengembalikan teks lebih sedikit. Mengembalikan satu baris per entri, diikuti totalnya. {ONLY}"),
    "list_directory_with_sizes|path": f"Direktori yang akan ditampilkan isinya. {P}",
    "list_directory_with_sizes|sortBy": "Urutkan entri berdasarkan nama atau ukuran",
    "directory_tree|": (
        "Mendapatkan tampilan pohon rekursif dari file dan direktori dalam bentuk struktur JSON. Setiap entri memuat "
        "'name', 'type' (file/directory), dan 'children' untuk direktori. File tidak memiliki array children, sedangkan "
        "direktori selalu memiliki array children (yang bisa kosong), kecuali pada tingkat terakhir ketika 'depth' "
        "membatasi pohon: direktori tersebut tidak dibaca dan tidak memiliki array children. Output diformat dengan "
        f"indentasi 2 spasi agar mudah dibaca. {ONLY}"),
    "directory_tree|path": f"Direktori yang menjadi akar pohon. {P}",
    "directory_tree|excludePatterns": EXCL,
    "directory_tree|depth": (
        "Berapa tingkat yang akan ditelusuri: 1 hanya menampilkan entri yang berada langsung di dalam path. Direktori pada "
        "tingkat terakhir tidak memiliki array children. Kosongkan untuk seluruh pohon."),
    "move_file|": (
        "Memindahkan atau mengganti nama file dan direktori. Dapat memindahkan file antardirektori sekaligus mengganti "
        "namanya dalam satu operasi. Jika tujuan sudah ada, operasi akan gagal. Berfungsi lintas direktori dan dapat "
        "digunakan untuk sekadar mengganti nama di dalam direktori yang sama. Sumber dan tujuan harus sama-sama berada di "
        "dalam direktori yang diizinkan."),
    "move_file|source": f"File atau direktori yang akan dipindahkan atau diganti namanya. {P}",
    "move_file|destination": f"Path barunya, termasuk nama; belum boleh ada apa pun di lokasi tersebut. {P}",
    "copy_file|": (
        "Menyalin file ke lokasi baru, tanpa membaca isinya ke dalam percakapan. Menyalin satu file biasa, dengan "
        "mempertahankan izin akses dan waktu modifikasinya; direktori tidak disalin. Jika tujuan sudah ada, operasi akan "
        "gagal: tool ini tidak pernah menimpa. Sumber dan tujuan harus sama-sama berada di dalam direktori yang diizinkan."),
    "copy_file|source": "File yang akan disalin",
    "copy_file|destination": "Lokasi tempat salinan dibuat; belum boleh ada apa pun di lokasi tersebut",
    "search_files|": (
        "Mencari file dan direktori berdasarkan NAMA, bukan berdasarkan isi: tool ini tidak pernah membaca atau mencari di "
        "dalam file. Tool ini menelusuri pohon di bawah 'path' dan mencocokkan pola glob dengan path setiap entri relatif "
        "terhadap 'path' (peka huruf besar-kecil). Gunakan '*.ext' untuk mencocokkan entri yang berada langsung di bawah "
        "'path', dan '**/*.ext' atau '**/name' untuk mencocokkan di kedalaman mana pun. Mengembalikan path lengkap dari "
        "semua item yang cocok. Sangat berguna untuk mencari file ketika Anda tidak tahu lokasi pastinya. Hanya mencari di "
        "dalam direktori yang diizinkan."),
    "search_files|path": f"Direktori tempat pencarian dilakukan. {P}",
    "search_files|pattern": (
        "Glob yang dicocokkan dengan path setiap entri relatif terhadap path, tidak pernah dengan isinya: '*.ts' cocok "
        "langsung di bawah path, '**/*.ts' di kedalaman mana pun."),
    "search_files|excludePatterns": EXCL,
    "get_file_info|": (
        "Mengambil metadata terperinci tentang file atau direktori. Mengembalikan informasi lengkap termasuk ukuran, waktu "
        "pembuatan, waktu terakhir diubah, izin akses, tipe, dan jumlah hard link. Tool ini sangat cocok untuk memahami "
        f"karakteristik file tanpa membaca isinya. {ONLY}"),
    "get_file_info|path": f"File atau direktori yang akan dideskripsikan. {P}",
    "list_allowed_directories|": (
        "Mengembalikan daftar direktori yang boleh diakses oleh server ini. Subdirektori di dalam direktori yang diizinkan "
        "ini juga dapat diakses. Gunakan ini untuk mengetahui direktori mana saja beserta path di dalamnya yang tersedia "
        "sebelum mencoba mengakses file."),
    # ---- memory ----
    "create_entities|": (
        "Membuat beberapa entitas baru di graf pengetahuan. Entitas yang namanya sudah ada, atau yang mengulang entitas "
        "sebelumnya dalam pemanggilan yang sama, akan dilewati dan observasinya tidak ditambahkan; hasilnya mencantumkan "
        "nama-nama yang dilewati di `skipped`. Gunakan add_observations untuk menambahkan observasi ke entitas yang sudah "
        "ada."),
    "create_entities|entities": "Entitas yang akan dibuat, masing-masing dengan nama yang unik di dalam graf",
    "create_relations|": (
        "Membuat beberapa relasi baru antarentitas di graf pengetahuan. Relasi harus dinyatakan dalam kalimat aktif"),
    "create_relations|relations": (
        "Relasi yang akan dibuat. Kedua ujungnya harus merujuk ke entitas yang sudah ada; relasi yang sudah ada di graf "
        "tidak ditambahkan lagi"),
    "add_observations|": "Menambahkan observasi baru ke entitas yang sudah ada di graf pengetahuan",
    "add_observations|observations": (
        "Observasi yang akan ditambahkan, dikelompokkan per entitas. Setiap entitas harus sudah ada; observasi yang sudah "
        "dimiliki entitas tersebut tidak ditambahkan lagi"),
    "delete_entities|": (
        "Menghapus entitas secara utuh dari graf pengetahuan, beserta setiap relasi yang mengarah ke atau dari entitas "
        "tersebut dan semua observasinya. Gunakan hanya untuk menghapus sebuah entitas sepenuhnya; untuk menghapus "
        "hubungan antara dua entitas tetapi mempertahankan keduanya, gunakan delete_relations, dan untuk menghapus fakta "
        "dari sebuah entitas, gunakan delete_observations. Tidak dapat dibatalkan."),
    "delete_entities|entityNames": "Array berisi nama entitas yang akan dihapus",
    "delete_observations|": "Menghapus observasi tertentu dari entitas di graf pengetahuan",
    "delete_observations|deletions": (
        "Observasi yang akan dihapus, dikelompokkan per entitas, masing-masing dicocokkan berdasarkan teksnya yang persis"),
    "delete_relations|": (
        "Menghapus relasi tertentu (from, to, relationType) dari graf pengetahuan dan mempertahankan entitas yang "
        "dihubungkannya. Setiap relasi harus sama persis dengan relasi yang ada pada ketiga field tersebut; jika ragu, "
        "panggil open_nodes (atau search_nodes) terlebih dahulu untuk membaca relationType yang tersimpan. Gunakan untuk "
        "menghapus hubungan antara dua entitas; untuk menghapus entitasnya sendiri, gunakan delete_entities. Tidak dapat "
        "dibatalkan."),
    "delete_relations|relations": "Array berisi relasi yang akan dihapus",
    "read_graph|": (
        "Membaca seluruh graf pengetahuan: setiap entitas beserta observasinya, dan setiap relasi. Hasilnya bertambah "
        "besar seiring bertambahnya graf, jadi gunakan ini hanya ketika Anda memerlukan semuanya; utamakan search_nodes "
        "untuk mencari entitas berdasarkan kata kunci dan open_nodes untuk membaca entitas yang namanya sudah Anda "
        "ketahui."),
    "read_graph|entityTypes": (
        "Hanya kembalikan entitas yang entityType-nya termasuk salah satu dari nilai ini (harus sama persis), dan hanya "
        "relasi yang menyentuh salah satu entitas tersebut. Kosongkan untuk mengembalikan semua entitas."),
    "read_graph|observationLimit": OBSLIM,
    "search_nodes|": (
        "Mencari entitas di graf pengetahuan yang nama, tipe, atau observasinya mengandung kueri (tidak peka huruf "
        "besar-kecil). Gunakan ini ketika Anda memiliki kata kunci, topik, atau sebagian nama, tetapi tidak mengetahui "
        "nama entitas yang persis. Utamakan open_nodes jika Anda sudah mengetahui nama yang persis, dan gunakan read_graph "
        "hanya jika Anda memerlukan seluruh graf. Mengembalikan entitas yang cocok dan setiap relasi yang menyentuh salah "
        "satunya."),
    "search_nodes|query": "Kueri pencarian yang dicocokkan dengan nama entitas, tipe, dan isi observasi",
    "search_nodes|limit": (
        "Kembalikan paling banyak sejumlah ini entitas yang cocok (kecocokan pertama, sesuai urutan penyimpanan), beserta "
        "relasi yang menyentuhnya. Kosongkan untuk mengembalikan semua kecocokan."),
    "search_nodes|observationLimit": OBSLIM,
    "open_nodes|": (
        "Mengambil entitas tertentu berdasarkan nama persisnya, beserta setiap relasi yang menyentuh salah satunya. "
        "Gunakan ini ketika Anda sudah mengetahui namanya (dari percakapan, atau dari hasil search_nodes atau read_graph "
        "sebelumnya); ini adalah cara termurah untuk membaca entitas yang dapat Anda sebutkan namanya. Utamakan "
        "search_nodes jika Anda hanya memiliki kata kunci atau sebagian nama. Nama yang tidak ada akan dilewati."),
    "open_nodes|names": "Array berisi nama entitas yang akan diambil",
    "open_nodes|observationLimit": OBSLIM,
    # ---- git ----
    "git_status|": "Menampilkan status working tree",
    "git_diff_unstaged|": "Menampilkan perubahan di direktori kerja yang belum di-stage",
    "git_diff_staged|": "Menampilkan perubahan yang sudah di-stage untuk commit",
    "git_diff|": ("Menampilkan perbedaan antar-branch atau antar-commit, atau dalam suatu rentang revisi "
                  "(main..feature, main...feature)"),
    "git_commit|": "Merekam perubahan ke repositori",
    "git_add|": "Menambahkan isi file ke staging area",
    "git_reset|": "Membatalkan stage semua perubahan yang sudah di-stage",
    "git_log|": "Menampilkan log commit",
    "git_log|max_count": "Jumlah maksimum commit yang ditampilkan. Minimal 1.",
    "git_log|start_timestamp": f"Timestamp awal untuk menyaring commit. {TS_EX}",
    "git_log|end_timestamp": f"Timestamp akhir untuk menyaring commit. {TS_EX}",
    "git_create_branch|": "Membuat branch baru dari branch atau commit dasar yang bersifat opsional",
    "git_create_branch|base_branch": (
        "Branch, tag, atau SHA commit yang menjadi dasar pembuatan branch. Bawaannya adalah branch saat ini, atau commit "
        "saat ini jika HEAD dalam keadaan detached"),
    "git_checkout|": "Berpindah branch",
    "git_merge|": (
        "Menggabungkan sebuah branch ke branch saat ini. Hanya fast-forward kecuali fast_forward_only bernilai false; "
        "menolak working tree yang kotor, dan membatalkan merge yang mengalami konflik sehingga repositori tidak berubah"),
    "git_merge|source_branch": "Branch, tag, atau commit yang akan digabungkan ke branch saat ini",
    "git_merge|fast_forward_only": (
        "Hanya fast-forward, dan gagal jika kedua branch sudah bercabang. False mengizinkan merge commit"),
    "git_show|": "Menampilkan isi sebuah commit, atau isi file atau direktori yang diberikan dalam bentuk <revision>:<path>",
    "git_branch|": "Menampilkan daftar branch Git",
    "git_branch|repo_path": "Path ke repositori Git.",
    "git_branch|branch_type": (
        "Apakah akan menampilkan branch lokal ('local'), branch remote ('remote'), atau semua branch ('all')."),
    "git_branch|contains": (
        "SHA commit yang harus dimuat oleh branch. Jangan isi parameter ini jika tidak ada SHA commit yang disebutkan"),
    "git_branch|not_contains": (
        "SHA commit yang TIDAK boleh dimuat oleh branch. Jangan isi parameter ini jika tidak ada SHA commit yang "
        "disebutkan"),
    "git_remote|": (
        "Menampilkan daftar remote repositori beserta URL fetch dan push-nya, seperti `git remote -v`. Kredensial yang "
        "tertanam di dalam URL ditampilkan sebagai <redacted>"),
    "git_remote|repo_path": "Path ke repositori Git.",
    # ---- fetch ----
    "fetch|": (
        "Mengambil sebuah URL dari internet dan secara opsional mengekstrak isinya sebagai markdown.\n\n"
        "Meskipun awalnya Anda tidak memiliki akses internet, dan disarankan untuk menolak serta memberi tahu pengguna "
        "tentang hal ini, tool ini sekarang memberi Anda akses internet. Sekarang Anda dapat mengambil informasi terbaru "
        "dan memberi tahu pengguna tentang hal itu."),
    "fetch|url": "URL yang akan diambil",
    "fetch|max_length": "Jumlah maksimum karakter yang dikembalikan.",
    "fetch|start_index": (
        "Kembalikan output mulai dari indeks karakter ini, berguna jika pengambilan sebelumnya terpotong dan diperlukan "
        "konteks tambahan."),
    "fetch|raw": "Dapatkan konten HTML asli dari halaman yang diminta, tanpa penyederhanaan.",
    "fetch|timeout_ms": (
        "Berapa lama menunggu, dalam milidetik, untuk terhubung ke server dan untuk setiap pembacaan responsnya sebelum "
        "menyerah. Naikkan nilainya untuk server yang lambat atau unduhan yang besar; turunkan agar cepat gagal."),
    # ---- time ----
    "get_current_time|": "Mendapatkan waktu saat ini di zona waktu tertentu",
    "get_current_time|timezone": TZ,
    "convert_time|": "Mengonversi waktu antarzona waktu",
    "convert_time|source_timezone": f"Nama zona waktu IANA sumber (misalnya, 'America/New_York', 'Europe/London'). {TZ_OPT}",
    "convert_time|time": "Waktu yang akan dikonversi dalam format 24 jam (HH:MM)",
    "convert_time|target_timezone": f"Nama zona waktu IANA tujuan (misalnya, 'Asia/Tokyo', 'America/San_Francisco'). {TZ_OPT}",
    "get_time_ago|": "Mendapatkan waktu sejumlah hari, jam, menit, dan detik yang lalu di zona waktu tertentu",
    "get_time_ago|timezone": TZ,
    "get_time_ago|days_ago": "Jumlah hari penuh sebelum sekarang",
    "get_time_ago|hours_ago": "Jumlah jam penuh sebelum sekarang",
    "get_time_ago|minutes_ago": "Jumlah menit penuh sebelum sekarang",
    "get_time_ago|seconds_ago": "Jumlah detik penuh sebelum sekarang",
}

with open("/kaggle/working/id_translations.json", "w", encoding="utf-8") as f:
    json.dump(ID, f, ensure_ascii=False, indent=2)
print(f"OK: {len(ID)} terjemahan")
