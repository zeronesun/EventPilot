/**
 * 简道云自动生成文档
 * 自动审查结果与建议
 */

export interface SuggestionItem {
  type: 'error' | 'warning' | 'info' | 'success';
  title: string;
  desc?: string;
  solution?: string;
  source: string;
}

export interface AutoReviewResult {
  totalErrors: number;
  totalWarnings: number;
  suggestions: SuggestionItem[];
}

export function generateAutoReview(result: AutoReviewResult): string {
  const suggestionsHtml = result.suggestions.map(item => {
    const icons = {
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
      success: '✅',
    }
    return `
### ${icons[item.type]} ${item.type.toUpperCase()}: ${item.title}

**描述：** ${item.desc || '无描述'}

${item.solution ? `**建议：** ${item.solution}\n` : ''}

**来源：** ${item.source}
`
  }).join('\n')

  return `
# 🔍 代码自动审查结果

## 📊 总体统计

- ❌ 错误：${result.totalErrors}
- ⚠️ 警告：${result.totalWarnings}
- ℹ️ 总数：${result.suggestions.length}

---

## 🔧 详细建议

${suggestionsHtml}
`
}

export function createReviewSummary(results: AutoReviewResult[]): string {
  const summaryHeader = `
# 🤖 Hermes Agent 代码自动审查

**审查时间：** ${new Date().toLocaleString('zh-CN')}
**审查范围：** EventPilot 项目代码库

`

  const reviewContent = results.map(result => generateAutoReview(result)).join('\n\n---\n\n')

  return summaryHeader + reviewContent
}
