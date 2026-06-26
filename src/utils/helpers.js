export const getDistance = (lat1, lon1, lat2, lon2) => {
      const R = 6371e3;
      const φ1 = lat1 * Math.PI / 180, φ2 = lat2 * Math.PI / 180;
      const Δφ = (lat2 - lat1) * Math.PI / 180, Δλ = (lon2 - lon1) * Math.PI / 180;
      const a = Math.sin(Δφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(Δλ/2)**2;
      return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    };

    export const getCategoryEmoji = (cat) =>
      ({ 'Elektronik': '📱', 'Tekstil': '👗', 'Mobilya': '🪑', 'Diğer': '📦' })[cat] ?? '📦';

    export const catName = (cat) => ({
      'Elektronik': window.currentLang === 'en' ? 'Electronics' : 'Elektronik',
      'Tekstil':    window.currentLang === 'en' ? 'Textile'     : 'Tekstil',
      'Mobilya':    window.currentLang === 'en' ? 'Furniture'   : 'Mobilya',
      'Diğer':      window.currentLang === 'en' ? 'Other'       : 'Diğer',
    })[cat] ?? cat;

    export const urgencyLabel = (ac) => ({
      'Düşük':  window.currentLang === 'en' ? 'LOW'    : 'DÜŞÜK',
      'Orta':   window.currentLang === 'en' ? 'MEDIUM' : 'ORTA',
      'Yüksek': window.currentLang === 'en' ? 'HIGH'   : 'YÜKSEK',
    })[ac] ?? ac;