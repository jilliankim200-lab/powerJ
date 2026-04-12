/**
 * _src_index.html    → dist/index.html   (+ index.dist.html)
 * qr-generator.html  → dist/qr-generator.html   (+ qr-generator.dist.html)
 * about/privacy/contact.html, robots.txt, sitemap.xml, logo.svg → dist/ (그대로 복사)
 * CSS 압축 + JS 난독화 + HTML 압축 + 소스 보호
 */
const fs = require('fs');
const path = require('path');
const JavaScriptObfuscator = require('javascript-obfuscator');
const { minify: htmlMinify } = require('html-minifier-terser');

const DIST_DIR = path.join(__dirname, 'dist');
// 난독화/빌드 없이 dist로 그대로 복사할 정적 파일 목록 (AdSense 정책 페이지 + SEO 파일)
const STATIC_ASSETS = [
    'about.html',
    'privacy.html',
    'contact.html',
    'guide.html',
    'templates.html',
    'gallery.html',
    'usecase.html',
    'qr-guide.html',
    'excel-tips.html',
    'googlefc5523fefa32702e.html',
    'robots.txt',
    'sitemap.xml',
    'logo.svg',
];

const OBFUSCATE_OPTIONS = {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.7,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.3,
    debugProtection: false,
    debugProtectionInterval: 0,
    disableConsoleOutput: true,
    identifierNamesGenerator: 'hexadecimal',
    log: false,
    numbersToExpressions: true,
    renameGlobals: false,
    selfDefending: false,
    simplify: true,
    splitStrings: true,
    splitStringsChunkLength: 5,
    stringArray: true,
    stringArrayCallsTransform: true,
    stringArrayEncoding: ['base64'],
    stringArrayIndexShift: true,
    stringArrayRotate: true,
    stringArrayShuffle: true,
    stringArrayWrappersCount: 2,
    stringArrayWrappersChainedCalls: true,
    stringArrayWrappersParametersMaxCount: 4,
    stringArrayWrappersType: 'function',
    stringArrayThreshold: 0.75,
    transformObjectKeys: true,
    unicodeEscapeSequence: false,
};

const PROTECTION_JS = `
(function(){
    document.addEventListener('contextmenu', function(e){ e.preventDefault(); });
    document.addEventListener('keydown', function(e){
        if(e.key==='F12') { e.preventDefault(); return false; }
        if(e.ctrlKey && e.shiftKey && (e.key==='I'||e.key==='J'||e.key==='C')) { e.preventDefault(); return false; }
        if(e.ctrlKey && e.key==='u') { e.preventDefault(); return false; }
    });
})();
`;

async function buildFile(src, out, label, distName) {
    let html = fs.readFileSync(src, 'utf-8');

    // 1) 인라인 <script> 태그 전체 난독화 (외부 src 스크립트는 건드리지 않음)
    html = html.replace(/<script>([\s\S]*?)<\/script>/g, (match, js) => {
        const fullJs = PROTECTION_JS + '\n' + js;
        const obfuscated = JavaScriptObfuscator.obfuscate(fullJs, OBFUSCATE_OPTIONS).getObfuscatedCode();
        return `<script>${obfuscated}</script>`;
    });

    // 2) CSS 압축
    html = html.replace(/<style>([\s\S]*?)<\/style>/g, (match, css) => {
        const minCss = css
            .replace(/\/\*[\s\S]*?\*\//g, '')
            .replace(/\s*\n\s*/g, '')
            .replace(/\s*{\s*/g, '{')
            .replace(/\s*}\s*/g, '}')
            .replace(/\s*:\s*/g, ':')
            .replace(/\s*;\s*/g, ';')
            .replace(/;}/g, '}');
        return `<style>${minCss}</style>`;
    });

    // 3) HTML 압축
    html = await htmlMinify(html, {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        minifyCSS: false,
        minifyJS: false,
    });

    // 4) 저작권 주석 추가
    html = `<!-- ${label} | All rights reserved | Unauthorized modification prohibited -->\n` + html;

    fs.writeFileSync(out, html, 'utf-8');

    // dist/ 폴더에도 배포용 파일명으로 함께 저장
    if (distName) {
        if (!fs.existsSync(DIST_DIR)) fs.mkdirSync(DIST_DIR, { recursive: true });
        fs.writeFileSync(path.join(DIST_DIR, distName), html, 'utf-8');
    }

    const srcSize = (fs.statSync(src).size / 1024).toFixed(1);
    const outSize = (fs.statSync(out).size / 1024).toFixed(1);
    console.log(`\n✓ [${label}] 빌드 완료`);
    console.log(`  원본: ${path.basename(src)} (${srcSize} KB)`);
    console.log(`  배포: ${path.basename(out)} (${outSize} KB)`);
    if (distName) console.log(`  dist: dist/${distName}`);
}

function copyStaticAssets() {
    if (!fs.existsSync(DIST_DIR)) fs.mkdirSync(DIST_DIR, { recursive: true });
    let copied = 0;
    for (const name of STATIC_ASSETS) {
        const src = path.join(__dirname, name);
        if (!fs.existsSync(src)) {
            console.warn(`  ⚠ ${name} 없음 — 건너뜀`);
            continue;
        }
        fs.copyFileSync(src, path.join(DIST_DIR, name));
        copied++;
    }
    console.log(`\n✓ 정적 파일 ${copied}/${STATIC_ASSETS.length}개 dist/에 복사 완료`);
}

async function build() {
    await buildFile(
        path.join(__dirname, '_src_index.html'),
        path.join(__dirname, 'index.dist.html'),
        'Dashboard Builder',
        'index.html'
    );

    await buildFile(
        path.join(__dirname, 'qr-generator.html'),
        path.join(__dirname, 'qr-generator.dist.html'),
        'QR / 바코드 생성기',
        'qr-generator.html'
    );

    copyStaticAssets();

    console.log(`\n보호 기능:`);
    console.log(`  - JavaScript 난독화 (변수/함수명 변환, 문자열 암호화, 제어흐름 변환)`);
    console.log(`  - 우클릭 차단`);
    console.log(`  - F12 / Ctrl+Shift+I / Ctrl+U 차단`);
    console.log(`  - 콘솔 출력 비활성화`);
    console.log(`\n⚠ *.dist.html 파일을 배포하세요. 원본은 보관용입니다.`);
}

build().catch(err => { console.error('빌드 실패:', err.message); process.exit(1); });
