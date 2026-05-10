/**
 * 合规词汇处理工具
 */

// 违规词汇列表
const FORBIDDEN_WORDS = [
  '排名', '排行榜', '快慢班', '好差生', '打卡',
  '每日必做', '必须完成', '重点班', '实验班'
]

// 替换词汇映射
const REPLACEMENTS: Record<string, string> = {
  '排名': '个人成长进度',
  '排行榜': '班级分布概况',
  '快慢班': '学习小组',
  '好差生': '不同学习阶段的学生',
  '打卡': '记录',
  '每日必做': '选做建议',
  '必须完成': '建议完成',
  '重点班': '特色班',
  '实验班': '特色班',
  '作业': '练习' // 仅在家长端替换
}

/**
 * 检查文本是否包含违规词
 */
export function checkCompliance(text: string): { valid: boolean; violations: string[] } {
  const violations: string[] = []
  
  for (const word of FORBIDDEN_WORDS) {
    if (text.includes(word)) {
      violations.push(word)
    }
  }
  
  return {
    valid: violations.length === 0,
    violations
  }
}

/**
 * 替换违规词
 */
export function sanitizeText(text: string, isParentView: boolean = false): string {
  let result = text
  
  for (const [old, newText] of Object.entries(REPLACEMENTS)) {
    // 家长端额外替换"作业"
    if (old === '作业' && !isParentView) {
      continue
    }
    result = result.replace(new RegExp(old, 'g'), newText)
  }
  
  return result
}

/**
 * 生成匿名化统计描述
 */
export function anonymizeStatistics(total: number, count: number): string {
  if (total === 0) {
    return '暂无数据'
  }
  
  const percentage = Math.round((count / total) * 100)
  
  if (percentage < 5) return '少数同学'
  if (percentage < 20) return '约10%的同学'
  if (percentage < 30) return '约20%的同学'
  if (percentage < 45) return '约35%的同学'
  if (percentage < 55) return '约半数同学'
  if (percentage < 70) return '约60%的同学'
  if (percentage < 85) return '约75%的同学'
  return '绝大多数同学'
}
