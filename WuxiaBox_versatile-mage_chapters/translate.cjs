#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Default configurations
let port = '11434';
let model = 'gemma4:cloud';
let rawArgs = [];

// Parse Command Line Arguments
const args = process.argv.slice(2);
for (let i = 0; i < args.length; i++) {
    if (args[i] === '-p') {
        port = args[++i];
    } else if (args[i] === '-m') {
        model = args[++i];
    } else if (args[i] !== '|') { // Ignore literal pipe character
        rawArgs.push(args[i]);
    }
}

// Helper to expand a range into individual numbers
function expandRange(start, end) {
    let nums = [];
    const min = Math.min(start, end);
    const max = Math.max(start, end);
    for (let i = min; i <= max; i++) {
        nums.push(i);
    }
    return nums;
}

// استخدام Set لمنع التكرار نهائياً وتجنب التداخل
let uniqueNumbers = new Set();

// المفسر الذكي الخالي من التداخل
for (let i = 0; i < rawArgs.length; i++) {
    const current = rawArgs[i];

    // الحالة 1: العنصر الحالي يحتوي على شرطة صريحة (مثل "4-5" أو "13-56")
    if (current.includes('-')) {
        const parts = current.split('-');
        parts.forEach(p => {
            const num = parseInt(p, 10);
            if (!isNaN(num)) uniqueNumbers.add(num);
        });
    } 
    // الحالة 2: العنصر الحالي عبارة عن رقم نقي
    else {
        const currentNum = parseInt(current, 10);
        if (!isNaN(currentNum)) {
            // التحقق: هل العنصر القادم موجود، وهو رقم نقي، ولا يحتوي على شرطة؟
            if (i + 1 < rawArgs.length && !rawArgs[i+1].includes('-')) {
                const nextNum = parseInt(rawArgs[i+1], 10);
                if (!isNaN(nextNum)) {
                    // إذاً هذا نطاق كامل (مثل "1 4")
                    expandRange(currentNum, nextNum).forEach(n => uniqueNumbers.add(n));
                    i++; // الـتعديل الحاسم: قفز خطوة للأمام لتخطي الرقم الثاني وعدم تكراره كملف منفرد
                    continue;
                }
            }
            
            // إذا لم يكن نطاقاً، يُعامل كملف منفرد محدد
            uniqueNumbers.add(currentNum);
        }
    }
}

// تحويل الـ Set إلى مصفوفة مرتبة تصاعدياً
let fileNumbers = Array.from(uniqueNumbers).sort((a, b) => a - b);

// Validate if any files were specified
if (fileNumbers.length === 0) {
    console.error("❌ Error: Please specify valid files or ranges (e.g., 1 4 5-10)");
    process.exit(1);
}

// Create 'AR' directory if it doesn't exist
const outputDir = path.join(process.cwd(), 'AR');
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

// Dynamic duration formatting function (ms, s, m, h)
function formatDuration(ms) {
    if (ms < 1000) return `${ms.toFixed(0)} ms`;
    
    let seconds = ms / 1000;
    if (seconds < 60) return `${seconds.toFixed(2)} s`;
    
    let minutes = seconds / 60;
    if (minutes < 60) {
        let remainingSeconds = seconds % 60;
        return `${Math.floor(minutes)} m ${remainingSeconds.toFixed(0)} s`;
    }
    
    let hours = minutes / 60;
    let remainingMinutes = minutes % 60;
    return `${Math.floor(hours)} h ${remainingMinutes.toFixed(0)} m`;
}

// Send payload request to Ollama quietly
async function translateText(content, fileName) {
    const url = `http://127.0.0.1:${port}/api/generate`;
    
    const prompt = `
You are an expert literary translator specializing in translating English novels into rich, contextual, and natural Arabic. 
I am providing you with a full chapter of a novel.

CRITICAL INSTRUCTIONS FOR NOVEL TRANSLATION:
1. Contextual Pronouns: Pay extreme attention to gender and numbers (هو, هي, أنتَ, أنتِ, أنتم, هما). Analyze the narrative context carefully to determine who is speaking to whom, or who is being described. Do not blindly use default masculine pronouns.
2. Tone & Flow: The translation must read like an authentic Arabic novel, preserving the emotional weight, metaphors, and literary tone. Avoid literal "Google Translate" style.
3. Think Twice: Double-check your choices before outputting. Ensure the dialogue feels natural for the character's gender and social dynamic.
4. Output Only: Return ONLY the final Arabic translation of the chapter. Do not include any introductory remarks, explanations, or notes.
5. No Repetition Loops: Never repeat characters, letters, words, or sound effects infinitely (e.g., do not spam letters like زيزززز or similar endlessly). Keep onomatopoeia concise and natural, and finish the chapter cleanly.

File Name: ${fileName}
Content to translate:
---------------------------
${content}
---------------------------
`;

    const requestBody = {
        model: model,
        prompt: prompt,
        stream: true,
        options: {
            temperature: 0.3,
            repeat_penalty: 1.15,
            num_predict: 4096
        }
    };

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
        throw new Error(`Ollama Server error: ${response.statusText}`);
    }

    let fullResponse = '';
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (line.trim() !== '') {
                try {
                    const parsed = JSON.parse(line);
                    if (parsed.response) {
                        // Silent collection: removed process.stdout.write here
                        fullResponse += parsed.response;
                    }
                } catch (e) {
                    // Ignore JSON parse errors on partial trailing chunks
                }
            }
        }
    }
    
    return fullResponse;
}

// Main Execution
async function main() {
    console.log(`🤖 Model: ${model} | 🔌 Port: ${port}`);
    console.log(`📂 Target Directory: ${outputDir}`);
    console.log(`📋 Files queue to be processed: ${fileNumbers.join(', ')}\n`);

    let successCount = 0;
    let failureCount = 0;

    for (const num of fileNumbers) {
        const fileName = `${num}.txt`;
        const filePath = path.join(process.cwd(), fileName);
        const outputPath = path.join(outputDir, fileName);

        console.log(`----------------------------------------`);
        console.log(`[${fileName}] ⏳ Status: Translating in background...`);

        if (!fs.existsSync(filePath)) {
            console.log(`[${fileName}] ❌ Request failed due to: log | Source file not found in current directory.`);
            failureCount++;
            continue;
        }

        const startTime = performance.now();

        try {
            const content = fs.readFileSync(filePath, 'utf-8');
            const translation = await translateText(content, fileName);
            
            fs.writeFileSync(outputPath, translation, 'utf-8');
            
            const endTime = performance.now();
            const durationFormatted = formatDuration(endTime - startTime);

            console.log(`[${fileName}] ✅ Completed and saved to: AR/${fileName} (${durationFormatted})`);
            successCount++;
        } catch (error) {
            console.log(`[${fileName}] ❌ Request failed due to: log | ${error.message}`);
            failureCount++;
        }
    }

    console.log(`========================================`);
    console.log(`🎉 Process Completed!`);
    console.log(`✅ Successful files count: ${successCount}`);
    console.log(`❌ Failed files count: ${failureCount}`);
}

main();
