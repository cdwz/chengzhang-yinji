/**
 * 成长印记 - 全局常量
 */

// 预置科目（系统默认三科）
export const PRESET_SUBJECTS = ['语文', '数学', '英语'] as const

// 常见自定义科目（供选择添加）
export const COMMON_SUBJECTS = [
  '科学', '道德与法治', '音乐', '美术', '体育', '信息技术', '其他'
] as const

// 所有科目（预置 + 常见，用于提示/验证）
export const ALL_KNOWN_SUBJECTS = [...PRESET_SUBJECTS, ...COMMON_SUBJECTS] as const

// 合规禁用词
export const COMPLIANCE_BANNED_WORDS = ['排名', '打卡', '必做', '作业']

// 评价类型
export const EVALUATION_TYPES = [
  { label: '⭐ 星级（1-5星）', value: 'star' },
  { label: '📝 等第（A/B/C/D）', value: 'grade' },
  { label: '🔢 分值', value: 'score' },
  { label: '📄 A/B卷分值', value: 'ab_score' },
  { label: '✅ 是否完成', value: 'boolean' },
  { label: '💬 文本备注', value: 'text' },
] as const

// 评价类型名称映射
export const EVALUATION_TYPE_NAMES: Record<string, string> = {
  star: '星级',
  grade: '等第',
  score: '分值',
  ab_score: 'A/B卷',
  boolean: '是否完成',
  text: '文本备注',
}

// 评价类型标签颜色映射
export const EVALUATION_TYPE_TAGS: Record<string, string> = {
  star: 'warning',
  grade: 'success',
  score: 'primary',
  ab_score: 'danger',
  boolean: 'info',
  text: 'info',
}

// 科目标签颜色
export const SUBJECT_COLORS: Record<string, string> = {
  '语文': '#e6a23c',
  '数学': '#67c23a',
  '英语': '#409eff',
  '科学': '#f56c6c',
  '道德与法治': '#909399',
  '音乐': '#e040fb',
  '美术': '#ff9800',
  '体育': '#4caf50',
  '信息技术': '#00bcd4',
  '其他': '#607d8b',
}
