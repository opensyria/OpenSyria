const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// PA-03 Security Fix: Static files with cache headers for performance
app.use(express.static(path.join(__dirname, 'public'), {
    maxAge: '1d',      // Cache static assets for 1 day
    etag: true,        // Enable ETags for cache validation
    lastModified: true // Enable Last-Modified headers
}));

// EJS setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Translations
const translations = {
  en: require('./locales/en'),
  ar: require('./locales/ar')
};

// Routes
app.get('/', (req, res) => {
  const lang = req.query.lang || 'en';
  const t = translations[lang] || translations.en;
  res.render('index', { t, lang, currentPage: 'home' });
});

app.get('/download', (req, res) => {
  const lang = req.query.lang || 'en';
  const t = translations[lang] || translations.en;
  res.render('download', { t, lang, currentPage: 'download' });
});

app.get('/community', (req, res) => {
  const lang = req.query.lang || 'en';
  const t = translations[lang] || translations.en;
  res.render('community', { t, lang, currentPage: 'community' });
});

app.get('/docs', (req, res) => {
  const lang = req.query.lang || 'en';
  const t = translations[lang] || translations.en;
  res.render('docs', { t, lang, currentPage: 'docs' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`OpenSY website running at http://localhost:${PORT}`);
});
