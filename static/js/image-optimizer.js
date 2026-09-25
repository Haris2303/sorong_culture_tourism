// Optimasi gambar di sisi browser sebelum diunggah: validasi berkas benar-benar
// gambar, resize ke dimensi maksimal, & konversi ke WebP. Tujuannya supaya
// request ke server jauh lebih kecil sehingga terhindar dari error 413
// (payload terlalu besar) saat admin mengunggah gambar wisata/budaya.
(function () {
  const DEFAULTS = { maxDimension: 1920, quality: 0.82, maxGaleriFiles: 12 };
  const cfg = Object.assign({}, DEFAULTS, window.ADMIN_UPLOAD_CONFIG || {});

  let webpSupportChecked = null;
  function supportsWebpEncoding() {
    if (webpSupportChecked !== null) return webpSupportChecked;
    try {
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      webpSupportChecked = canvas.toDataURL('image/webp').startsWith('data:image/webp');
    } catch (e) {
      webpSupportChecked = false;
    }
    return webpSupportChecked;
  }

  function loadBitmap(file) {
    if (window.createImageBitmap) {
      return createImageBitmap(file);
    }
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const img = new Image();
      img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('decode-failed')); };
      img.src = url;
    });
  }

  // Kompres+konversi satu berkas. Return {file} kalau sukses, {error} kalau
  // berkas ditolak (bukan gambar valid / gagal didekode / gagal dikompres).
  async function optimizeImageFile(file) {
    if (!file.type || !file.type.startsWith('image/')) {
      return { error: `'${file.name}' bukan berkas gambar.` };
    }

    let bitmap;
    try {
      bitmap = await loadBitmap(file);
    } catch (e) {
      return { error: `'${file.name}' gagal dibaca sebagai gambar (berkas rusak?).` };
    }

    const srcW = bitmap.width, srcH = bitmap.height;
    if (!srcW || !srcH) {
      return { error: `'${file.name}' gagal dibaca sebagai gambar (berkas rusak?).` };
    }

    const scale = Math.min(1, cfg.maxDimension / Math.max(srcW, srcH));
    const targetW = Math.max(1, Math.round(srcW * scale));
    const targetH = Math.max(1, Math.round(srcH * scale));

    const canvas = document.createElement('canvas');
    canvas.width = targetW;
    canvas.height = targetH;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0, targetW, targetH);
    if (bitmap.close) bitmap.close();

    const useWebp = supportsWebpEncoding();
    const mimeType = useWebp ? 'image/webp' : 'image/jpeg';
    const extension = useWebp ? 'webp' : 'jpg';

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, mimeType, cfg.quality));
    if (!blob) {
      return { error: `'${file.name}' gagal dikompres di browser, coba gambar lain.` };
    }

    const baseName = file.name.replace(/\.[^.]+$/, '') || 'gambar';
    return { file: new File([blob], `${baseName}.${extension}`, { type: mimeType }) };
  }

  // Kompres banyak berkas sekaligus, batasi jumlah maksimal (galeri).
  async function optimizeFileList(fileList, { maxCount } = {}) {
    const files = Array.from(fileList || []);
    const rejected = [];
    let truncated = false;

    let accepted = files;
    if (maxCount && files.length > maxCount) {
      truncated = true;
      accepted = files.slice(0, maxCount);
    }

    const optimized = [];
    for (const file of accepted) {
      const result = await optimizeImageFile(file);
      if (result.error) {
        rejected.push(result.error);
      } else {
        optimized.push(result.file);
      }
    }
    return { files: optimized, rejected, truncated };
  }

  // Hitung berapa banyak kompresi yang sedang berjalan per <form> (gambar
  // utama & galeri bisa dikompres bersamaan), supaya tombol submit cuma
  // aktif lagi setelah SEMUA proses kompresi pada form itu selesai.
  const pendingByForm = new WeakMap();

  function beginCompressing(form, submitBtn) {
    if (!form || !submitBtn) return;
    const count = (pendingByForm.get(form) || 0) + 1;
    pendingByForm.set(form, count);
    if (count === 1) {
      if (submitBtn.dataset.idleHtml === undefined) {
        submitBtn.dataset.idleHtml = submitBtn.innerHTML;
      }
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>Mengompres gambar...';
    }
  }

  function endCompressing(form, submitBtn) {
    if (!form || !submitBtn) return;
    const count = Math.max(0, (pendingByForm.get(form) || 1) - 1);
    pendingByForm.set(form, count);
    if (count === 0) {
      submitBtn.disabled = false;
      if (submitBtn.dataset.idleHtml !== undefined) {
        submitBtn.innerHTML = submitBtn.dataset.idleHtml;
      }
    }
  }

  function isCompressing(form) {
    return !!form && (pendingByForm.get(form) || 0) > 0;
  }

  // Pasang optimisasi otomatis pada satu <input type="file">: begitu admin
  // memilih gambar, langsung dikompres+dikonversi ke WebP, lalu ditampilkan
  // alert kalau ada berkas yang ditolak/terpotong karena melewati batas.
  function attachImageOptimizer(inputId, nameId, options = {}) {
    const input = document.getElementById(inputId);
    const nameEl = document.getElementById(nameId);
    if (!input || !nameEl) return;

    const maxCount = options.multiple ? (options.maxCount || cfg.maxGaleriFiles) : 1;
    const emptyText = options.emptyText || 'Belum ada file dipilih';
    const form = input.closest('form');
    const submitBtn = form ? form.querySelector('.form-actions button[type="submit"]') : null;

    input.addEventListener('change', async () => {
      if (!input.files || input.files.length === 0) {
        nameEl.textContent = emptyText;
        return;
      }

      nameEl.textContent = 'Mengompres gambar...';
      beginCompressing(form, submitBtn);

      let result;
      try {
        result = await optimizeFileList(input.files, { maxCount });
      } finally {
        endCompressing(form, submitBtn);
      }

      const dt = new DataTransfer();
      result.files.forEach((f) => dt.items.add(f));
      input.files = dt.files;

      if (result.files.length === 0) {
        nameEl.textContent = emptyText;
      } else if (result.files.length === 1) {
        nameEl.textContent = result.files[0].name;
      } else {
        nameEl.textContent = `${result.files.length} file dipilih (sudah dikompres)`;
      }

      if (result.rejected.length) {
        alert(`Berkas berikut dilewati karena bukan gambar yang valid:\n- ${result.rejected.join('\n- ')}`);
      }
      if (result.truncated) {
        alert(`Maksimal ${maxCount} foto galeri per unggahan. Hanya ${maxCount} foto pertama yang dipakai.`);
      }
    });
  }

  function totalFileSize(...fileLists) {
    let total = 0;
    fileLists.forEach((list) => {
      Array.from(list || []).forEach((f) => { total += f.size; });
    });
    return total;
  }

  window.ImageOptimizer = { attachImageOptimizer, optimizeFileList, totalFileSize, isCompressing, config: cfg };
})();
