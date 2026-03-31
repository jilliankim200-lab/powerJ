/**
 * dashboard.html → dashboard.dist.html
 * CSS 압축 + JS 난독화 + HTML 압축 + 소스 보호
 */
const fs = require('fs');
const path = require('path');
const JavaScriptObfuscator = require('javascript-obfuscator');
const { minify: htmlMinify } = require('html-minifier-terser');

const SRC = path.join(__dirname, '_src_index.html');
const OUT = path.join(__dirname, 'index.dist.html');

async function build() {
    let html = fs.readFileSync(SRC, 'utf-8');

    // 1) JS 추출 및 난독화
    const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
    if (scriptMatch) {
        const originalJs = scriptMatch[1];

        // 우클릭/개발자도구 차단 + 소스 보호 코드 추가
        const protectionJs = `
// Source Protection
(function(){
    // 우클릭 차단
    document.addEventListener('contextmenu', function(e){ e.preventDefault(); });
    // 개발자도구 단축키 차단
    document.addEventListener('keydown', function(e){
        if(e.key==='F12') { e.preventDefault(); return false; }
        if(e.ctrlKey && e.shiftKey && (e.key==='I'||e.key==='J'||e.key==='C')) { e.preventDefault(); return false; }
        if(e.ctrlKey && e.key==='u') { e.preventDefault(); return false; }
    });
    // 개발자도구 감지
    var t=0;
    setInterval(function(){
        var s=performance.now();
        debugger;
        if(performance.now()-s>100){
            document.body.innerHTML='<div style="display:flex;align-items:center;justify-content:center;height:100vh;background:#161717;color:#F43F5E;font-family:Pretendard,sans-serif;font-size:20px;font-weight:700">Unauthorized access detected.</div>';
        }
    },3000);
})();
`;
        const fullJs = protectionJs + '\n' + originalJs;

        // 난독화
        const obfuscated = JavaScriptObfuscator.obfuscate(fullJs, {
            compact: true,
            controlFlowFlattening: true,
            controlFlowFlatteningThreshold: 0.7,
            deadCodeInjection: true,
            deadCodeInjectionThreshold: 0.3,
            debugProtection: true,
            debugProtectionInterval: 2000,
            disableConsoleOutput: true,
            identifierNamesGenerator: 'hexadecimal',
            log: false,
            numbersToExpressions: true,
            renameGlobals: false,
            selfDefending: true,
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
        }).getObfuscatedCode();

        html = html.replace(/<script>[\s\S]*?<\/script>/, `<script>${obfuscated}</script>`);
    }

    // 2) CSS 압축 (간단 처리)
    html = html.replace(/<style>([\s\S]*?)<\/style>/, (match, css) => {
        const minCss = css
            .replace(/\/\*[\s\S]*?\*\//g, '')    // 주석 제거
            .replace(/\s*\n\s*/g, '')             // 줄바꿈 제거
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
        minifyCSS: false,  // 이미 처리함
        minifyJS: false,   // 이미 난독화 처리함
    });

    // 4) 저작권 주석 추가
    const header = `<!-- Dashboard Builder | All rights reserved | Unauthorized modification prohibited -->\n`;
    html = header + html;

    fs.writeFileSync(OUT, html, 'utf-8');

    const srcSize = (fs.statSync(SRC).size / 1024).toFixed(1);
    const outSize = (fs.statSync(OUT).size / 1024).toFixed(1);
    console.log(`\n✓ 빌드 완료`);
    console.log(`  원본: dashboard.html (${srcSize} KB)`);
    console.log(`  배포: dashboard.dist.html (${outSize} KB)`);
    console.log(`\n보호 기능:`);
    console.log(`  - JavaScript 난독화 (변수/함수명 변환, 문자열 암호화, 제어흐름 변환)`);
    console.log(`  - 우클릭 차단`);
    console.log(`  - F12 / Ctrl+Shift+I / Ctrl+U 차단`);
    console.log(`  - 개발자도구 감지 시 화면 차단`);
    console.log(`  - 콘솔 출력 비활성화`);
    console.log(`  - 디버거 보호`);
    console.log(`\n⚠ dashboard.dist.html 을 배포하세요. 원본(dashboard.html)은 보관용입니다.`);
}

build().catch(err => { console.error('빌드 실패:', err.message); process.exit(1); });
