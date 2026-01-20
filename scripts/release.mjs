import fs from 'fs';
import path from 'path';
import { execSync, spawn } from 'child_process';
import readline from 'readline/promises';
import { fileURLToPath } from 'url';

/**
 * DouDouChat Release Script
 * 自动打包并上传到 GitHub Release
 */

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const log = (msg) => console.log(`\x1b[36m[Release]\x1b[0m ${msg}`);
const logSuccess = (msg) => console.log(`\x1b[32m[Success]\x1b[0m ${msg}`);
const logError = (msg) => console.error(`\x1b[31m[Error]\x1b[0m ${msg}`);

async function main() {
    process.on('SIGINT', () => {
        rl.close();
        process.exit(0);
    });

    try {
        log('开始自动发布流程...');

        // 1. 检查环境变量或从控制台请求 Token
        let token = process.env.GITHUB_TOKEN;
        if (!token) {
            logError('未在环境变量中找到 GITHUB_TOKEN。');
            token = await rl.question('请输入你的 GitHub Personal Access Token (或回车跳过但可能无法上传): ');
            token = token.trim();
        }

        // 2. 获取版本信息
        const pkgPath = path.join(rootDir, 'package.json');
        if (!fs.existsSync(pkgPath)) {
            throw new Error(`找不到 package.json: ${pkgPath}`);
        }
        const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
        const currentVersion = pkg.version;
        log(`当前项目版本: ${currentVersion}`);

        // 3. 计算自动增量版本
        let nextVersion = '';
        const parts = currentVersion.split('.');
        if (parts.length === 3) {
            const patch = parseInt(parts[2]) || 0;
            parts[2] = (patch + 1).toString();
            nextVersion = parts.join('.');
        } else {
            nextVersion = currentVersion + '.1';
        }

        // 4. 输入版本号
        const userVersion = await rl.question(`请输入发布版本号 [默认: ${nextVersion}]: `);
        const version = userVersion.trim() || nextVersion;

        // 5. 输入更新日志
        const notes = await rl.question('请输入本次更新的功能点 (支持多行，输入完成后连按两次回车): \n');
        let releaseNotes = notes;
        // 如果想要支持多行，可以用更复杂的逻辑，这里简化一下

        // 6. 更新 package.json
        if (version !== currentVersion) {
            pkg.version = version;
            fs.writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n', 'utf8');
            logSuccess(`已更新 package.json 版本号为 ${version}`);

            // 同步版本号到 front/package.json
            log('正在同步版本号到子模块...');
            try {
                execSync('node scripts/sync-version.cjs', { cwd: rootDir, stdio: 'inherit' });
            } catch (e) {
                logError('版本同步失败，但将继续：' + e.message);
            }
        }

        // 7. 执行打包脚本
        log(`正在打包应用 (执行 scripts\\package-electron.bat)...`);
        const buildProcess = spawn('cmd.exe', ['/c', 'scripts\\package-electron.bat'], {
            cwd: rootDir,
            stdio: 'inherit'
        });

        const buildExitCode = await new Promise((resolve) => {
            buildProcess.on('close', resolve);
        });

        if (buildExitCode !== 0) {
            throw new Error('打包脚本执行失败，请检查上方日志。');
        }

        logSuccess('打包完成！');

        // 8. 寻找构建产物
        const distDir = path.join(rootDir, 'dist-electron');
        if (!fs.existsSync(distDir)) {
            throw new Error(`找不到 dist-electron 目录，打包可能未按预期生成产物。`);
        }

        const files = fs.readdirSync(distDir);
        // 寻找 exe 安装包
        const exeFile = files.find(f => f.startsWith('WeAgentChat Setup') && f.endsWith('.exe'));

        if (!exeFile) {
            throw new Error('未在 dist-electron/ 目录中找到 WeAgentChat Setup *.exe 文件。');
        }

        const filePath = path.join(distDir, exeFile);
        log(`找到发布目标文件: ${exeFile}`);

        // 9. 确认发布
        if (!token) {
            logError('由于没有 GitHub Token，流程将在此结束。你可以手动上传产物。');
            process.exit(0);
        }

        const confirm = await rl.question(`\n确认将产物上传到 GitHub Release v${version}? (y/n): `);
        if (confirm.toLowerCase() !== 'y') {
            log('发布已取消，构建产物保留在本地。');
            process.exit(0);
        }

        // 10. 解析仓库信息
        let owner = '';
        let repo = '';
        try {
            const remoteUrl = execSync('git remote get-url origin', { encoding: 'utf8' }).trim();
            const match = remoteUrl.match(/github\.com[:/](.+)\/(.+?)(\.git)?$/);
            if (match) {
                owner = match[1];
                repo = match[2];
            }
        } catch (e) {
            logError('无法从 Git 配置中解析仓库地址。');
            const repoManual = await rl.question('请手动输入 GitHub 仓库路径 (格式 owner/repo): ');
            [owner, repo] = repoManual.split('/');
        }

        if (!owner || !repo) {
            throw new Error('仓库信息获取失败。');
        }

        log(`目标仓库: https://github.com/${owner}/${repo}`);
        log('正在创建 GitHub Release...');

        // 11. 创建 GitHub Release
        const releaseResponse = await fetch(`https://api.github.com/repos/${owner}/${repo}/releases`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tag_name: `v${version}`,
                name: `v${version}`,
                body: releaseNotes || `Release v${version}`,
                draft: false,
                prerelease: false
            })
        });

        const releaseData = await releaseResponse.json();
        if (!releaseResponse.ok) {
            throw new Error(`创建 Release 失败: ${releaseData.message || JSON.stringify(releaseData)}`);
        }

        logSuccess(`Release 创建成功: ${releaseData.html_url}`);

        // 12. 上传附件
        const uploadUrlStr = releaseData.upload_url.split('{')[0];
        const uploadUrl = `${uploadUrlStr}?name=${encodeURIComponent(exeFile)}`;

        log(`开始上传二进制文件: ${exeFile}...`);
        const fileBuffer = fs.readFileSync(filePath);

        const uploadResponse = await fetch(uploadUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28',
                'Content-Type': 'application/octet-stream',
                'Content-Length': fileBuffer.length
            },
            body: fileBuffer
        });

        const uploadData = await uploadResponse.json();
        if (uploadResponse.ok) {
            logSuccess('✅ 附件上传成功！发布流程全部完成。');
            log(`查看 Release: ${releaseData.html_url}`);
        } else {
            throw new Error(`上传附件失败: ${uploadData.message || JSON.stringify(uploadData)}`);
        }

    } catch (error) {
        logError(`发生错误: ${error.message}`);
    } finally {
        rl.close();
    }
}

main();
