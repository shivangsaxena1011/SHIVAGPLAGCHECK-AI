const fs = require('fs');
const path = require('path');

const srcDir = path.join(__dirname, '.next');
const destParent = path.join(__dirname, 'frontend');
const destDir = path.join(destParent, '.next');

if (fs.existsSync(srcDir)) {
  try {
    if (!fs.existsSync(destParent)) {
      fs.mkdirSync(destParent, { recursive: true });
    }
    fs.cpSync(srcDir, destDir, { recursive: true });
    console.log('Successfully mirrored .next to frontend/.next for Vercel output compatibility.');
  } catch (err) {
    console.warn('Postbuild mirroring warning:', err.message);
  }
}
