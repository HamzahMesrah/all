const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");
const readline = require("readline");

const SITE_CONFIGS = {
    "1": {
        name: "WuxiaBox",
        baseUrl: "https://www.wuxiabox.com/novel/",
        selector: ".chapter-content"
    },
    "2": {
        name: "FanMTL",
        baseUrl: "https://www.fanmtl.com/novel/",
        selector: ".chapter-content"
    }
};

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function ask(question) {
    return new Promise(resolve => {
        rl.question(question, answer => resolve(answer.trim()));
    });
}

async function downloadChapter(siteConfig, id, chapter, outputDir) {
    const url = `${siteConfig.baseUrl}${id}_${chapter}.html`;

    console.log(`\nDownloading chapter ${chapter}...`);
    console.log(url);

    try {
        const response = await fetch(url, {
            headers: {
                "User-Agent": "Mozilla/5.0"
            }
        });

        if (!response.ok) {
            const errMsg = `Chapter ${chapter}: HTTP ${response.status}`;
            console.log(errMsg);
            return { chapter, error: errMsg };
        }

        const html = await response.text();
        const $ = cheerio.load(html);

        const content = $(siteConfig.selector).first();

        if (!content.length) {
            const errMsg = `Chapter ${chapter}: ${siteConfig.selector} not found.`;
            console.log(errMsg);
            return { chapter, error: errMsg };
        }

        // إزالة الإعلانات والـ scripts
        content.find("script, style, iframe").remove();

        // استخراج النص مع الحفاظ على فواصل الفقرات
        let text = "";

        content.find("p").each((i, el) => {
            const paragraph = $(el)
                .text()
                .replace(/\s+/g, " ")
                .trim();

            if (paragraph) {
                text += paragraph + "\n\n";
            }
        });

        // في حالة وجود نص ليس داخل <p>
        if (!text.trim()) {
            text = content
                .text()
                .replace(/\s+/g, " ")
                .trim();
        }

        text = text.trim();

        if (!text) {
            const errMsg = `Chapter ${chapter}: empty content.`;
            console.log(errMsg);
            return { chapter, error: errMsg };
        }

        // إنشاء مجلد الفصول
        fs.mkdirSync(outputDir, { recursive: true });

        // اسم الملف = رقم الفصل فقط
        const filePath = path.join(
            outputDir,
            `${chapter}.txt`
        );

        fs.writeFileSync(filePath, text, "utf8");

        console.log(`Saved: ${filePath}`);

        return {
            chapter,
            text
        };

    } catch (error) {
        const errMsg = `Chapter ${chapter}: ${error.message}`;
        console.log(errMsg);
        return { chapter, error: errMsg };
    }
}

async function main() {
    console.log("=== Novel Chapter Downloader ===\n");
    console.log("Select a site:");
    for (const [key, config] of Object.entries(SITE_CONFIGS)) {
        console.log(`${key}. ${config.name}`);
    }

    const siteChoice = await ask("Choice: ");
    const siteConfig = SITE_CONFIGS[siteChoice];

    if (!siteConfig) {
        console.log("Invalid site choice.");
        rl.close();
        return;
    }

    console.log(`\nUsing ${siteConfig.name}\n`);

    const args = process.argv.slice(2);
    let id, firstChapter, lastChapter;

    if (args.length >= 3) {
        // Usage: node install.cjs {id} {first_num} {last_num}
        id = args[0];
        firstChapter = parseInt(args[1], 10);
        lastChapter = parseInt(args[2], 10);
    } else if (args.length === 2) {
        // Usage: node install.cjs {first_num} {last_num}
        firstChapter = parseInt(args[0], 10);
        lastChapter = parseInt(args[1], 10);
        id = await ask("Novel ID: ");
    } else {
        // Interactive mode
        id = await ask("Novel ID: ");
        firstChapter = parseInt(await ask("First chapter: "), 10);
        lastChapter = parseInt(await ask("Last chapter: "), 10);
    }

    if (!id || isNaN(firstChapter) || isNaN(lastChapter)) {
        console.log("Invalid input.");
        rl.close();
        return;
    }

    if (firstChapter > lastChapter) {
        console.log("First chapter must be <= last chapter.");
        rl.close();
        return;
    }

    const outputDir = path.join(
        __dirname,
        `${siteConfig.name}_${id}_chapters`
    );

    const allChapters = [];
    const failedChapters = [];

    for (
        let chapter = firstChapter;
        chapter <= lastChapter;
        chapter++
    ) {
        const result = await downloadChapter(
            siteConfig,
            id,
            chapter,
            outputDir
        );

        if (result && result.text) {
            allChapters.push(result);
        } else if (result && result.error) {
            failedChapters.push(result);
        }

        // تأخير بسيط بين الطلبات
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    // إنشاء الملف الكبير
    if (allChapters.length > 0) {
        let combined = "";

        for (let i = 0; i < allChapters.length; i++) {
            const chapter = allChapters[i];

            combined += `Chapter ${chapter.chapter}\n\n`;
            combined += chapter.text;

            if (i < allChapters.length - 1) {
                combined += "\n\n_____\n\n";
            }
        }

        const combinedPath = path.join(
            __dirname,
            "data.txt"
        );

        fs.writeFileSync(
            combinedPath,
            combined,
            "utf8"
        );

        console.log("\n==============================");
        console.log("Finished!");
        console.log(`Individual files: ${outputDir}`);
        console.log(`Combined file: ${combinedPath}`);
        console.log("==============================");
    } else {
        console.log("\nNo chapters were downloaded.");

    }

    // Report any chapters that failed to download
    if (failedChapters && failedChapters.length > 0) {
        console.log("\nSome chapters failed to download:");
        failedChapters.forEach(f => {
            console.log(`- Chapter ${f.chapter}: ${f.error}`);
        });

        // Write error log file
        const errorLogPath = path.join(__dirname, "error_log.txt");
        const errorLogContent = failedChapters
            .map(f => `Chapter ${f.chapter}: ${f.error}`)
            .join("\n");
        fs.writeFileSync(errorLogPath, errorLogContent, "utf8");
        console.log(`Error log written to ${errorLogPath}`);
    }
    rl.close();
}

main();
