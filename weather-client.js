/**
 * Dual-source trip weather (NWS grid forecast + Open-Meteo) with localStorage cache.
 * Init via TripWeather.init(opts) from itinerary or weather.html.
 */
(function (global) {
  'use strict';

  var TZ = 'America/Denver';
  var CACHE_PREFIX = 'wca-weather-cache-v1-';
  var TTL_MS = 90 * 60 * 1000;
  var NWS_DELAY_MS = 150;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function denverYmd(ms) {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date(ms));
  }

  function parseWindMph(windStr) {
    if (!windStr || typeof windStr !== 'string') return null;
    var m = windStr.match(/(\d+)\s*(?:to|-|–)\s*(\d+)/i);
    if (m) return Math.max(parseInt(m[1], 10), parseInt(m[2], 10));
    m = windStr.match(/(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  }

  function nwsMapClickUrl(lat, lon) {
    return 'https://forecast.weather.gov/MapClick.php?lat=' + lat + '&lon=' + lon;
  }


  function openMeteoDocsUrl() {
    return 'https://open-meteo.com/en/docs';
  }

  function sleep(ms) {
    return new Promise(function (r) {
      setTimeout(r, ms);
    });
  }

  var gridUrlCache = Object.create(null);

  function pickNwsDaySummary(forecastJson, dateIso) {
    var periods = (forecastJson.properties && forecastJson.properties.periods) || [];
    var dayPs = periods.filter(function (p) {
      return denverYmd(new Date(p.startTime).getTime()) === dateIso;
    });
    if (!dayPs.length) return null;
    var temps = dayPs.map(function (p) {
      return p.temperature;
    }).filter(function (t) {
      return typeof t === 'number';
    });
    if (!temps.length) return null;
    var hi = Math.max.apply(null, temps);
    var lo = Math.min.apply(null, temps);
    var pops = dayPs
      .map(function (p) {
        return (p.probabilityOfPrecipitation && p.probabilityOfPrecipitation.value) || 0;
      })
      .filter(function (x) {
        return typeof x === 'number';
      });
    var pop = pops.length ? Math.max.apply(null, pops) : null;
    var dayPart = dayPs.find(function (p) {
      return p.isDaytime;
    });
    var first = dayPs[0];
    var shortForecast = (dayPart && dayPart.shortForecast) || first.shortForecast || '';
    var windSpeed = (dayPart && dayPart.windSpeed) || first.windSpeed || '';
    var windMph = parseWindMph(windSpeed);
    return {
      hi: hi,
      lo: lo,
      pop: pop,
      shortForecast: shortForecast,
      windSpeed: windSpeed,
      windMph: windMph,
    };
  }

  function fetchNwsForLatLon(lat, lon, dateIso) {
    var key = lat + ',' + lon;
    return Promise.resolve()
      .then(function () {
        if (gridUrlCache[key]) return gridUrlCache[key];
        return fetch('https://api.weather.gov/points/' + lat + ',' + lon, {
          headers: { Accept: 'application/geo+json' },
        }).then(function (r) {
          if (!r.ok) throw new Error('NWS points HTTP ' + r.status);
          return r.json();
        }).then(function (j) {
          var url = j.properties && j.properties.forecast;
          if (!url) throw new Error('NWS: no forecast URL');
          gridUrlCache[key] = url;
          return url;
        });
      })
      .then(function (forecastUrl) {
        return fetch(forecastUrl, { headers: { Accept: 'application/geo+json' } });
      })
      .then(function (r) {
        if (!r.ok) throw new Error('NWS forecast HTTP ' + r.status);
        return r.json();
      })
      .then(function (fj) {
        var sum = pickNwsDaySummary(fj, dateIso);
        if (!sum) return { error: 'No NWS period for ' + dateIso, summary: null };
        return { error: null, summary: sum };
      });
  }

  function fetchOpenMeteoDay(lat, lon, dateIso) {
    var q =
      'https://api.open-meteo.com/v1/forecast?latitude=' +
      encodeURIComponent(lat) +
      '&longitude=' +
      encodeURIComponent(lon) +
      '&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,weathercode' +
      '&start_date=' +
      encodeURIComponent(dateIso) +
      '&end_date=' +
      encodeURIComponent(dateIso) +
      '&timezone=' +
      encodeURIComponent(TZ) +
      '&temperature_unit=fahrenheit&wind_speed_unit=mph';
    return fetch(q)
      .then(function (r) {
        if (!r.ok) throw new Error('Open-Meteo HTTP ' + r.status);
        return r.json();
      })
      .then(function (j) {
        var d = j.daily || {};
        var t = (d.time && d.time[0]) || null;
        if (t !== dateIso) throw new Error('Open-Meteo date mismatch');
        return {
          hi: d.temperature_2m_max && d.temperature_2m_max[0],
          lo: d.temperature_2m_min && d.temperature_2m_min[0],
          pop: d.precipitation_probability_max && d.precipitation_probability_max[0],
          windMph: d.wind_speed_10m_max && d.wind_speed_10m_max[0],
          weathercode: d.weathercode && d.weathercode[0],
        };
      });
  }

  function buildConcerns(nws, om) {
    var out = [];
    var pop = null;
    if (om && om.pop != null) pop = om.pop;
    if (pop == null && nws && nws.pop != null) pop = nws.pop;
    if (pop != null && pop >= 40) {
      out.push('Elevated rain chance (' + pop + '%) — gravel turns greasy and the lookout spurs get slick.');
    }
    var wind = null;
    if (om && om.windMph != null) wind = om.windMph;
    if (wind == null && nws && nws.windMph != null) wind = nws.windMph;
    if (wind != null && wind >= 25) {
      out.push('Breezy / windy (to ~' + Math.round(wind) + ' mph) — watch for falling limbs in timber and exposure at the lookouts.');
    }
    var hi = null;
    if (om && om.hi != null) hi = om.hi;
    if (hi == null && nws && nws.hi != null) hi = nws.hi;
    if (hi != null && hi >= 90) out.push('Hot daytime — extra water, and expect high fire danger and possible restrictions.');
    var lo = null;
    if (om && om.lo != null) lo = om.lo;
    if (lo == null && nws && nws.lo != null) lo = nws.lo;
    if (lo != null && lo <= 36) out.push('Near or below freezing overnight — normal for the 4,000 ft camps in September. Bring a real sleeping bag and expect frost on the tents.');
    var txt = ((nws && nws.shortForecast) || '').toLowerCase();
    if (/thunder|t-storm|lightning/.test(txt)) {
      out.push('Thunder risk in NWS wording — get off the exposed lookouts (High Rock, Burley, Council Bluff) and out of the lava caves.');
    }
    if (/snow|sleet|ice|wintry/.test(txt)) {
      out.push('Winter mix possible — check Babyshoe Pass and the High Rock spur, and verify US 12 / White Pass before the drive home.');
    }
    // Concern strings are HTML-escaped before rendering, so write plain text here.
    if (!out.length) out.push('No major automated flags — still check NWS alerts and the fire & closures page.');
    return out;
  }

  function mergeHi(n, o) {
    if (o && o.hi != null) return Math.round(Number(o.hi));
    if (n && n.hi != null) return n.hi;
    return null;
  }
  function mergeLo(n, o) {
    if (o && o.lo != null) return Math.round(Number(o.lo));
    if (n && n.lo != null) return n.lo;
    return null;
  }
  function mergePop(n, o) {
    if (o && o.pop != null) return o.pop;
    if (n && n.pop != null) return n.pop;
    return null;
  }
  function mergeWindMph(n, o) {
    if (o && o.windMph != null) return Number(o.windMph);
    if (n && n.windMph != null) return n.windMph;
    return null;
  }

  function teaserText(n, o) {
    if (n && n.shortForecast) {
      var s = n.shortForecast;
      return s.length <= 160 ? s : s.slice(0, 157) + '…';
    }
    if (o && (o.hi != null || o.lo != null)) {
      return (
        'Open-Meteo daily: hi/lo ' +
        (o.hi != null ? Math.round(o.hi) : '—') +
        '°/' +
        (o.lo != null ? Math.round(o.lo) : '—') +
        '°F' +
        (o.pop != null ? ' · PoP ' + o.pop + '%' : '') +
        (o.windMph != null ? ' · wind to ~' + Math.round(o.windMph) + ' mph' : '') +
        '.'
      );
    }
    return 'Forecast unavailable for this snapshot.';
  }

  function kpiV(innerHtml) {
    return '<span class="v">' + innerHtml + '</span>';
  }
  function kpiCell(label, innerHtml) {
    return (
      '<div class="wx-kpi-item"><span class="k">' +
      esc(label) +
      '</span>' +
      innerHtml +
      '</div>'
    );
  }

  function readCache(variantKey) {
    try {
      var raw = localStorage.getItem(CACHE_PREFIX + variantKey);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }

  function writeCache(variantKey, payload) {
    try {
      localStorage.setItem(CACHE_PREFIX + variantKey, JSON.stringify(payload));
    } catch (e) {}
  }

  function renderDaySlot(el, row, cachedDay, liveMeta) {
    row = row || {};
    var loc = el.querySelector('.day-weather-loc');
    var dyn = el.querySelector('.day-weather-dynamic');
    if (loc) {
      loc.textContent =
        (row.location_label || '') + (row.date_iso ? ' · ' + row.date_iso : '');
    }
    if (!dyn) return;
    if (!cachedDay) {
      dyn.className = 'day-weather-dynamic muted';
      dyn.innerHTML =
        '<span class="muted">' +
        (liveMeta && liveMeta.loading
          ? 'Loading forecasts…'
          : 'No cached data yet. Connect to refresh when you want numbers for this leg.') +
        '</span>';
      return;
    }
    var n = cachedDay.nws && cachedDay.nws.summary;
    var o = cachedDay.openMeteo;
    var concerns = cachedDay.concerns || [];
    var hi = mergeHi(n, o);
    var lo = mergeLo(n, o);
    var pop = mergePop(n, o);
    var wind = mergeWindMph(n, o);

    var hiInner = hi == null ? kpiV('—') : kpiV(hi + '°');
    var loInner = lo == null ? kpiV('—') : kpiV(lo + '°');
    var popInner = pop == null ? kpiV('—') : kpiV(pop + '%');
    var windInner =
      wind == null
        ? kpiV('—')
        : kpiV('~' + Math.round(wind) + '<span class="mph"> mph</span>');

    var kpiHtml =
      '<div class="wx-kpi" aria-label="Key forecast numbers">' +
      kpiCell('Hi', hiInner) +
      kpiCell('Lo', loInner) +
      kpiCell('Rain', popInner) +
      kpiCell('Wind', windInner) +
      '</div>';

    var teaser = '<p class="wx-teaser">' + esc(teaserText(n, o)) + '</p>';

    var cHtml =
      '<div class="wx-concerns"><strong>Concerns</strong><ul>' +
      (concerns && concerns.length
        ? concerns
            .map(function (c) {
              return '<li>' + esc(c) + '</li>';
            })
            .join('')
        : '<li class="muted">None flagged by automated checks.</li>') +
      '</ul></div>';

    var nwsHref = (cachedDay.links && cachedDay.links.nws) || '';
    var linkBits = [
      '<a href="' + esc(nwsHref) + '" target="_blank" rel="noopener">NWS point forecast</a>',
      '<a href="' + esc(openMeteoDocsUrl()) + '" target="_blank" rel="noopener">Open-Meteo docs</a>',
    ];
    var linkRow = '<p class="wx-link-row">' + linkBits.join(' · ') + '</p>';

    var nwsFull =
      n
        ? '<p><strong>NWS:</strong> ' +
          esc(n.shortForecast) +
          ' Hi/lo ' +
          n.hi +
          '°/' +
          n.lo +
          '°F' +
          (n.pop != null ? ' · PoP ' + n.pop + '%' : '') +
          (n.windSpeed ? ' · Wind ' + esc(n.windSpeed) + '.' : '.') +
          '</p>'
        : '<p class="muted"><strong>NWS:</strong> ' +
          esc((cachedDay.nws && cachedDay.nws.error) || '—') +
          '</p>';
    var omFull = o
      ? '<p><strong>Open-Meteo (daily):</strong> Hi/lo ' +
        (o.hi != null ? Math.round(o.hi) : '—') +
        '°/' +
        (o.lo != null ? Math.round(o.lo) : '—') +
        '°F' +
        (o.pop != null ? ' · PoP ' + o.pop + '%' : '') +
        (o.windMph != null ? ' · Wind to ~' + Math.round(o.windMph) + ' mph.' : '.') +
        '</p>'
      : '<p class="muted"><strong>Open-Meteo:</strong> —</p>';

    var detailsHtml =
      '<details class="wx-details">' +
      '<summary>Full NWS + Open-Meteo text</summary>' +
      '<div class="wx-details-inner">' +
      nwsFull +
      omFull +
      '</div></details>';

    var stamp = cachedDay.fetchedAt
      ? '<p class="muted weather-stamp">Snapshot: ' + esc(cachedDay.fetchedAt) + '</p>'
      : '';

    dyn.className = 'day-weather-dynamic';
    dyn.innerHTML = kpiHtml + teaser + cHtml + linkRow + detailsHtml + stamp;
  }

  function renderWeatherPageTable(tbody, daysRows, byDayId, liveMeta) {
    if (!tbody) return;
    tbody.innerHTML = '';
    daysRows.forEach(function (row) {
      var d = byDayId[row.day_id] || {};
      var tr = document.createElement('tr');
      var c1 = document.createElement('td');
      c1.innerHTML =
        '<strong>' +
        esc(row.trip_label || row.day_id) +
        '</strong><div class="muted">' +
        esc(row.date_iso) +
        '</div><div class="muted">' +
        esc(row.location_label) +
        '</div>';
      var c2 = document.createElement('td');
      var c3 = document.createElement('td');
      var c4 = document.createElement('td');
      var cached = d;
      if (cached && cached.nws && cached.nws.summary) {
        var s = cached.nws.summary;
        c2.textContent =
          s.shortForecast + ' · Hi/lo ' + s.hi + '°/' + s.lo + '°F' + (s.pop != null ? ' · PoP ' + s.pop + '%' : '');
      } else if (cached && cached.nws && cached.nws.error) {
        c2.textContent = cached.nws.error;
      } else {
        c2.textContent = '—';
      }
      if (cached && cached.openMeteo) {
        var o = cached.openMeteo;
        c3.textContent =
          'Hi/lo ' +
          (o.hi != null ? Math.round(o.hi) : '—') +
          '°/' +
          (o.lo != null ? Math.round(o.lo) : '—') +
          '°F' +
          (o.pop != null ? ' · PoP ' + o.pop + '%' : '') +
          (o.windMph != null ? ' · Wind ~' + Math.round(o.windMph) + ' mph' : '');
      } else {
        c3.textContent = '—';
      }
      if (cached && cached.concerns && cached.concerns.length) {
        c4.innerHTML =
          '<ul class="weather-concerns-tight">' +
          cached.concerns
            .map(function (x) {
              return '<li>' + esc(x) + '</li>';
            })
            .join('') +
          '</ul>';
      } else {
        c4.textContent = '—';
      }
      tr.appendChild(c1);
      tr.appendChild(c2);
      tr.appendChild(c3);
      tr.appendChild(c4);
      tbody.appendChild(tr);
    });
    var statusEl = document.getElementById('weather-status');
    if (statusEl) {
      var parts = [];
      if (liveMeta && liveMeta.fromCache) parts.push('Showing cached data');
      if (liveMeta && liveMeta.fetchedAt) parts.push('last fetch ' + liveMeta.fetchedAt);
      if (liveMeta && liveMeta.offline) parts.push('offline');
      if (liveMeta && liveMeta.refreshError) parts.push('refresh error: ' + liveMeta.refreshError);
      statusEl.textContent = parts.join(' · ') || (navigator.onLine ? 'Ready' : 'Offline');
    }
  }

  function fetchAllDays(days, variantKey, onProgress) {
    var byDay = {};
    var chain = Promise.resolve();
    days.forEach(function (row) {
      chain = chain.then(function () {
        return sleep(NWS_DELAY_MS).then(function () {
          return Promise.all([
            fetchNwsForLatLon(row.lat, row.lon, row.date_iso).catch(function (e) {
              return { error: String(e.message || e), summary: null };
            }),
            fetchOpenMeteoDay(row.lat, row.lon, row.date_iso).catch(function () {
              return null;
            }),
          ]).then(function (pair) {
            var nwsResult = pair[0];
            var om = pair[1];
            var nwsSummary = nwsResult && nwsResult.summary ? nwsResult.summary : null;
            var nwsErr = nwsResult && nwsResult.error ? nwsResult.error : null;
            var concerns = buildConcerns(nwsSummary, om);
            if (!nwsSummary && !om) {
              concerns = ['Both forecast sources failed — try Refresh when online.'];
            }
            var links = { nws: nwsMapClickUrl(row.lat, row.lon) };
            byDay[row.day_id] = {
              nws: {
                error: nwsSummary ? null : nwsErr || 'NWS unavailable',
                summary: nwsSummary,
              },
              openMeteo: om,
              concerns: concerns,
              links: links,
              fetchedAt: new Date().toLocaleString(),
            };
            if (onProgress) onProgress(row.day_id, byDay[row.day_id]);
          });
        });
      });
    });
    return chain.then(function () {
      return byDay;
    });
  }

  function mergeCachedDays(prevByDay, nextByDay) {
    var out = Object.assign({}, prevByDay || {}, nextByDay || {});
    return out;
  }

  function init(opts) {
    opts = opts || {};
    var variantKey = opts.variantKey || 'main';
    var days = opts.days || [];
    var mode = opts.mode || 'itinerary';
    var allVariants = opts.allVariants || null;

    function applyCacheToUI(cacheObj, liveMeta) {
      var byDay = (cacheObj && cacheObj.days) || {};
      if (mode === 'itinerary') {
        document.querySelectorAll('[data-day-weather]').forEach(function (el) {
          var id = el.getAttribute('data-day-weather');
          renderDaySlot(el, days.find(function (d) {
            return d.day_id === id;
          }) || { day_id: id }, byDay[id], liveMeta);
        });
      } else if (mode === 'weather_page') {
        var tbody = document.getElementById('weather-trip-tbody');
        var activeDays = (allVariants && allVariants[variantKey]) || days;
        renderWeatherPageTable(tbody, activeDays, byDay, liveMeta);
      }
    }

    var existing = readCache(variantKey);
    var initialMeta = {
      fromCache: !!existing,
      fetchedAt: existing && existing.fetchedAt,
      offline: !navigator.onLine,
      loading: false,
    };
    if (existing && existing.days) applyCacheToUI(existing, initialMeta);

    function runRefresh() {
      if (!navigator.onLine) {
        applyCacheToUI(existing || { days: {} }, {
          fromCache: true,
          offline: true,
          refreshError: 'Cannot refresh while offline',
        });
        return Promise.resolve();
      }
      var meta = { loading: true, offline: false };
      applyCacheToUI(existing || { days: {} }, meta);
      return fetchAllDays(days, variantKey, function (dayId, dayObj) {
        var partial = readCache(variantKey) || { days: {} };
        partial.days = partial.days || {};
        partial.days[dayId] = dayObj;
        partial.fetchedAt = new Date().toISOString();
        writeCache(variantKey, partial);
        applyCacheToUI(partial, { loading: true });
      }).then(function (freshPartial) {
        var prev = (existing && existing.days) || {};
        var merged = { days: mergeCachedDays(prev, freshPartial), fetchedAt: new Date().toISOString() };
        writeCache(variantKey, merged);
        applyCacheToUI(merged, {
          fromCache: false,
          fetchedAt: new Date().toLocaleString(),
          offline: false,
        });
      }).catch(function (e) {
        applyCacheToUI(existing || { days: {} }, {
          fromCache: !!existing,
          refreshError: String(e.message || e),
          offline: !navigator.onLine,
        });
      });
    }

    var btn = document.getElementById('weather-refresh');
    if (btn) {
      btn.addEventListener('click', function () {
        runRefresh();
      });
    }

    if (mode === 'weather_page' && allVariants) {
      var sel = document.getElementById('weather-variant-select');
      if (sel) {
        sel.value = variantKey;
        sel.addEventListener('change', function () {
          var v = sel.value;
          var u = new URL(global.location.href);
          u.searchParams.set('variant', v);
          global.location.href = u.pathname + u.search;
        });
      }
    }

    if (navigator.onLine) {
      runRefresh();
    } else {
      applyCacheToUI(existing || { days: {} }, {
        fromCache: !!existing,
        offline: true,
        refreshError: existing ? null : 'No cache yet — open online once',
      });
    }

    global.addEventListener('online', function () {
      runRefresh();
    });
  }

  global.TripWeather = { init: init };
})(typeof window !== 'undefined' ? window : this);
