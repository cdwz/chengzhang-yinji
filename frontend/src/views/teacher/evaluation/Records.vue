<template>
  <div class="evaluation-records-page">
    <!-- 筛选栏 -->
    <van-cell-group inset class="filter-section">
      <van-field
        v-model="selectedClassLabel"
        is-link
        readonly
        label="班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
      <van-field
        v-model="selectedSubject"
        is-link
        readonly
        label="科目"
        placeholder="全部科目"
        @click="showSubjectPicker = true"
      />
      <van-field
        v-model="selectedGroupLabel"
        is-link
        readonly
        label="组别"
        placeholder="全部组别"
        @click="showGroupPicker = true"
      />
      <van-field
        v-model="dateRangeText"
        is-link
        readonly
        label="日期范围"
        placeholder="选择日期范围"
        @click="showDateRangePicker = true"
      />
    </van-cell-group>

    <!-- 评价记录列表 -->
    <div class="section-title">评价记录</div>
    
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="loadRecords"
      >
        <van-cell-group inset>
          <van-swipe-cell v-for="record in records" :key="record.id">
            <van-cell :title="record.student_name" :label="getRecordLabel(record)" @click="openRecordDetail(record)">
              <template #icon>
                <van-tag :color="getSubjectColor(record.dimension.subject)" size="medium" style="margin-right: 8px;">
                  {{ record.dimension.subject || '通用' }}
                </van-tag>
              </template>
              <template #value>
                <div class="record-value">
                  {{ formatEvaluationValue(record) }}
                </div>
              </template>
            </van-cell>
            <template #right>
              <van-button square type="primary" text="编辑" @click="editRecord(record)" />
              <van-button square type="danger" text="删除" @click="deleteRecord(record.id)" />
            </template>
          </van-swipe-cell>
        </van-cell-group>
        
        <van-empty v-if="!loading && records.length === 0" description="暂无评价记录" />
      </van-list>
    </van-pull-refresh>

    <!-- 班级选择器 -->
    <van-popup v-model:show="showClassPicker" position="bottom" round>
      <van-picker
        :columns="classColumns"
        title="选择班级"
        @confirm="onClassConfirm"
        @cancel="showClassPicker = false"
      />
    </van-popup>

    <!-- 科目选择器 -->
    <van-popup v-model:show="showSubjectPicker" position="bottom" round>
      <van-picker
        :columns="subjectColumns"
        title="选择科目"
        @confirm="onSubjectConfirm"
        @cancel="showSubjectPicker = false"
      />
    </van-popup>

    <!-- 组别选择器 -->
    <van-popup v-model:show="showGroupPicker" position="bottom" round>
      <van-picker
        :columns="groupColumns"
        title="选择组别"
        @confirm="onGroupConfirm"
        @cancel="showGroupPicker = false"
      />
    </van-popup>

    <!-- 日期范围选择器 -->
    <van-popup v-model:show="showDateRangePicker" position="bottom" round>
      <van-date-picker
        v-model="datePickerValue"
        type="daterange"
        title="选择日期范围"
        @confirm="onDateRangeConfirm"
        @cancel="showDateRangePicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { http } from '@/utils/request'
import { getClasses } from '@/api/schools'
import { EVALUATION_TYPE_NAMES, SUBJECT_COLORS } from '@/constants'
import type { Class, StudyGroup, EvaluationRecord as ApiEvaluationRecord, EvaluationDimension } from '@/api/types'

// 扩展的评价记录类型
interface EvaluationRecord extends Omit<ApiEvaluationRecord, 'dimension'> {
  student_name: string
  dimension: Partial<EvaluationDimension> & {
    id: string
    name: string
    subject: string
    type: string
    config: Record<string, any>
  }
}

// 状态
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const records = ref<EvaluationRecord[]>([])
const classes = ref<Class[]>([])
const studyGroups = ref<StudyGroup[]>([])
const availableSubjects = ref<string[]>(['语文', '数学', '英语'])

// 筛选
const selectedClassId = ref('')
const selectedClassLabel = ref('')
const selectedSubject = ref('')
const selectedGroupId = ref('')
const selectedGroupLabel = ref('')
const dateFrom = ref('')
const dateTo = ref('')

// 弹窗
const showClassPicker = ref(false)
const showSubjectPicker = ref(false)
const showGroupPicker = ref(false)
const showDateRangePicker = ref(false)
const datePickerValue = ref(['2024-01-01', '2024-12-31'])

// 日期范围文本
const dateRangeText = computed(() => {
  if (!dateFrom.value && !dateTo.value) return ''
  if (dateFrom.value && dateTo.value) return `${dateFrom.value} 至 ${dateTo.value}`
  if (dateFrom.value) return `${dateFrom.value} 至今`
  if (dateTo.value) return `至 ${dateTo.value}`
  return ''
})

// 选择器列
const classColumns = computed(() => classes.value.map(c => ({ text: c.name, value: c.id })))
const subjectColumns = computed(() => {
  const cols = [{ text: '全部科目', value: '' }]
  availableSubjects.value.forEach(s => cols.push({ text: s, value: s }))
  return cols
})
const groupColumns = computed(() => {
  const cols = [{ text: '全部组别', value: '' }]
  studyGroups.value.forEach(g => cols.push({ text: g.name, value: g.id }))
  return cols
})

// 获取科目颜色
const getSubjectColor = (subject: string) => SUBJECT_COLORS[subject] || '#909399'

// 加载评价记录
const loadRecords = async () => {
  try {
    const params: any = {}
    if (selectedClassId.value) {
      params.class_id = selectedClassId.value
    }
    if (selectedSubject.value) {
      params.subject = selectedSubject.value
    }
    if (selectedGroupId.value) {
      params.group_id = selectedGroupId.value
    }
    if (dateFrom.value) {
      params.date_from = dateFrom.value
    }
    if (dateTo.value) {
      params.date_to = dateTo.value
    }
    
    const res = await http.get<EvaluationRecord[]>('/evaluations/records', { params })
    records.value = res
    finished.value = true
  } catch (error) {
    showFailToast('加载失败')
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 加载班级和科目
const loadClasses = async () => {
  try {
    classes.value = await getClasses()
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
      selectedClassLabel.value = classes.value[0].name
      availableSubjects.value = classes.value[0].subjects || ['语文', '数学', '英语']
      await loadStudyGroups()
      await loadRecords()
    }
  } catch (error) {
    showFailToast('加载班级失败')
  }
}

// 加载学习小组
const loadStudyGroups = async () => {
  if (!selectedClassId.value) return
  try {
    const res = await http.get<StudyGroup[]>(`/schools/classes/${selectedClassId.value}/groups`)
    studyGroups.value = res || []
  } catch {
    studyGroups.value = []
  }
}

// 下拉刷新
const onRefresh = () => {
  finished.value = false
  loadRecords()
}

// 获取记录标签
const getRecordLabel = (record: EvaluationRecord) => {
  const parts = [
    record.date || '未指定日期',
    record.dimension.name,
    EVALUATION_TYPE_NAMES[record.dimension.type] || record.dimension.type
  ]
  return parts.join(' · ')
}

// 格式化评价值
const formatEvaluationValue = (record: EvaluationRecord) => {
  const { type, config } = record.dimension
  const value = record.value
  
  if (!value) return '-'
  
  switch (type) {
    case 'star':
      return '⭐'.repeat(Number(value)) || '无'
    case 'grade':
      const gradeMap: Record<string, string> = { 'A': '优', 'B': '良', 'C': '中', 'D': '需努力' }
      return gradeMap[value] || value
    case 'score':
      return `${value}${config?.score_type === '10' ? '分' : '分'}`
    case 'ab_score':
      return `A${record.a_score || 0}/B${record.b_score || 0}`
    case 'boolean':
      return value ? '✅ 完成' : '❌ 未完成'
    case 'text':
      return value.length > 10 ? value.slice(0, 10) + '...' : value
    default:
      return value
  }
}

// 打开记录详情
const openRecordDetail = (record: EvaluationRecord) => {
  // 可扩展为详情弹窗
  console.log('打开详情', record)
}

// 编辑记录
const editRecord = (record: EvaluationRecord) => {
  // 可跳转到编辑页面或打开弹窗
  console.log('编辑记录', record)
}

// 删除记录
const deleteRecord = async (recordId: string) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '删除后无法恢复，确定要删除吗？'
    })
    
    await http.delete(`/evaluations/records/${recordId}`)
    showSuccessToast('删除成功')
    records.value = records.value.filter(r => r.id !== recordId)
  } catch (error) {
    if (error !== 'cancel') {
      showFailToast('删除失败')
    }
  }
}

// 选择器回调
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClassId.value = selected.value
  selectedClassLabel.value = selected.text
  showClassPicker.value = false
  selectedSubject.value = ''
  selectedGroupId.value = ''
  selectedGroupLabel.value = ''
  
  const cls = classes.value.find(c => c.id === selectedClassId.value)
  availableSubjects.value = cls?.subjects || ['语文', '数学', '英语']
  
  loadStudyGroups()
  loadRecords()
}

const onSubjectConfirm = ({ selectedOptions }: any) => {
  selectedSubject.value = selectedOptions[0].value
  showSubjectPicker.value = false
  loadRecords()
}

const onGroupConfirm = ({ selectedOptions }: any) => {
  selectedGroupId.value = selectedOptions[0].value
  selectedGroupLabel.value = selectedOptions[0].text
  showGroupPicker.value = false
  loadRecords()
}

const onDateRangeConfirm = ({ selectedValues }: any) => {
  dateFrom.value = selectedValues[0]
  dateTo.value = selectedValues[1]
  showDateRangePicker.value = false
  loadRecords()
}

onMounted(async () => {
  await loadClasses()
})
</script>

<style scoped lang="scss">
.evaluation-records-page {
  padding: 12px;
  padding-bottom: 80px;
  
  .filter-section {
    margin: 12px 0;
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .record-value {
    font-size: 16px;
    font-weight: 600;
    color: #3e7dc9;
    white-space: nowrap;
  }
}
</style>