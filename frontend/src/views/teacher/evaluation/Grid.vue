<template>
  <div class="evaluation-grid">
    <!-- 日期和班级选择 -->
    <van-cell-group inset class="header-section">
      <van-field
        v-model="selectedDate"
        is-link
        readonly
        label="评价日期"
        placeholder="选择日期"
        @click="showDatePicker = true"
      />
      <van-field
        v-model="selectedClass"
        is-link
        readonly
        label="选择班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
      <!-- 新增：科目筛选 -->
      <van-field
        v-model="selectedSubject"
        is-link
        readonly
        label="科目"
        placeholder="全部科目"
        @click="showSubjectPicker = true"
      />
      <!-- 新增：组别筛选 -->
      <van-field
        v-model="selectedGroupLabel"
        is-link
        readonly
        label="组别"
        placeholder="全部组别"
        @click="showGroupPicker = true"
      />
    </van-cell-group>

    <!-- 评价维度选择 -->
    <div class="section-title">评价维度</div>
    <van-cell-group inset class="dimension-section">
      <van-radio-group v-model="selectedDimensionId" direction="horizontal">
        <van-radio
          v-for="dim in dimensions"
          :key="dim.id"
          :name="dim.id"
          shape="square"
        >
          {{ dim.name }}
        </van-radio>
      </van-radio-group>
    </van-cell-group>

    <!-- 学生评价表格 -->
    <div v-if="selectedDimensionId" class="section-title">学生评价</div>
    
    <div v-if="selectedDimensionId" class="grid-container">
      <van-cell-group inset>
        <!-- 表头 -->
        <div class="grid-header">
          <div class="grid-cell student-cell">学生姓名</div>
          <div class="grid-cell rating-cell">评价</div>
          <div class="grid-cell action-cell">操作</div>
        </div>
        
        <!-- 表体 -->
        <div
          v-for="(student, index) in students"
          :key="student.id"
          :ref="el => { if (el) rowRefs[index] = el as HTMLElement }"
          class="grid-row"
          :class="{ 'has-value': evaluations[student.id], 'focused': focusedIndex === index }"
          tabindex="0"
          @keydown="handleKeyDown($event, index)"
          @focus="focusedIndex = index"
        >
          <div class="grid-cell student-cell">
            <span class="student-name">{{ student.name }}</span>
            <van-tag v-if="student.study_group_id" type="primary">
              {{ getGroupName(student.study_group_id) }}
            </van-tag>
          </div>
          
          <div class="grid-cell rating-cell">
            <StarInput v-if="currentDimension?.type === 'star'" v-model="evaluations[student.id]" />
            <GradeInput v-else-if="currentDimension?.type === 'grade'" v-model="evaluations[student.id]" />
            <ScoreInput v-else-if="currentDimension?.type === 'score'" v-model="evaluations[student.id]" :score-type="currentDimension?.config?.score_type || '100'" :max-score="currentDimension?.config?.max_score || 100" />
            <ABScoreInput v-else-if="currentDimension?.type === 'ab_score'" v-model="evaluations[student.id]" :total="currentDimension?.config?.total || 150" :a-max="currentDimension?.config?.a_score || 100" :b-max="currentDimension?.config?.b_score || 50" />
            <BooleanInput v-else-if="currentDimension?.type === 'boolean'" v-model="evaluations[student.id]" />
            <TextInput v-else-if="currentDimension?.type === 'text'" v-model="evaluations[student.id]" />
            <van-field v-else v-model="evaluations[student.id]" placeholder="输入评价" />
          </div>
          
          <div class="grid-cell action-cell">
            <van-button
              size="small"
              type="primary"
              :disabled="!evaluations[student.id]"
              @click="saveSingle(student.id)"
            >
              保存
            </van-button>
          </div>
        </div>
      </van-cell-group>
      
      <!-- 批量操作 -->
      <div class="batch-actions">
        <van-button type="default" :loading="copying" @click="copyFromYesterday" style="margin-bottom: 12px">
          <van-icon name="description" /> 复制前一天数据
        </van-button>
        <van-button type="default" @click="showBatchAssign = true" style="margin-bottom: 12px">
          <van-icon name="edit" /> 全部设为
        </van-button>
        <van-button type="primary" block :loading="saving" @click="saveAll">
          批量保存评价
        </van-button>
      </div>
    </div>

    <!-- 快捷评价模板 -->
    <div v-if="selectedDimensionId" class="section-title">快捷评语</div>
    <van-cell-group v-if="selectedDimensionId" inset class="templates-section">
      <van-tag
        v-for="tpl in quickTemplates"
        :key="tpl"
        size="medium"
        type="primary"
        plain
        class="template-tag"
        @click="applyTemplate(tpl)"
      >
        {{ tpl }}
      </van-tag>
    </van-cell-group>

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="datePickerValue"
        title="选择日期"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

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

    <!-- 批量赋值弹窗 -->
    <van-dialog v-model:show="showBatchAssign" title="全部设为" show-cancel-button @confirm="doBatchAssign">
      <div style="padding: 16px">
        <p style="margin-bottom:8px;color:#909399;font-size:13px">为所有学生设置相同的评价值</p>
        <van-field v-model="batchValue" placeholder="输入评价值" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { getClasses } from '@/api/schools'
import { getStudents, getStudyGroups } from '@/api/students'
import { getDimensions, getEvaluations, saveEvaluation, saveBatchEvaluations } from '@/api/evaluations'
import type { Class, Student, EvaluationDimension, StudyGroup } from '@/api/types'

// 状态
const classes = ref<Class[]>([])
const students = ref<Student[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const evaluations = reactive<Record<string, any>>({})
const saving = ref(false)
const copying = ref(false)
const showBatchAssign = ref(false)

// 科目和组别
const availableSubjects = ref<string[]>([])
const studyGroups = ref<StudyGroup[]>([])

// 键盘导航
const rowRefs = ref<HTMLElement[]>([])
const focusedIndex = ref(-1)

// 选择
const selectedDate = ref(new Date().toISOString().split('T')[0])
const selectedClass = ref('')
const selectedClassId = ref('')
const selectedSubject = ref('')
const selectedGroupId = ref('')
const selectedGroupLabel = ref('')
const selectedDimensionId = ref('')
const showDatePicker = ref(false)
const showClassPicker = ref(false)
const showSubjectPicker = ref(false)
const showGroupPicker = ref(false)
const datePickerValue = ref(['2024', '01', '01'])

// 快捷评语模板
const quickTemplates = [
  '认真完成',
  '积极主动',
  '进步明显',
  '需要加强',
  '继续保持',
  '表现优秀'
]

// 班级选择器列
const classColumns = computed(() => {
  return classes.value.map(c => ({
    text: c.name,
    value: c.id
  }))
})

// 科目选择器列
const subjectColumns = computed(() => {
  const cols = [{ text: '全部科目', value: '' }]
  availableSubjects.value.forEach(s => cols.push({ text: s, value: s }))
  return cols
})

// 组别选择器列
const groupColumns = computed(() => {
  const cols = [{ text: '全部组别', value: '' }]
  studyGroups.value.forEach(g => cols.push({ text: g.name, value: g.id }))
  return cols
})

// 获取当前维度的类型
const currentDimension = computed(() => {
  return dimensions.value.find(d => d.id === selectedDimensionId.value)
})

// 加载班级列表
const loadClasses = async () => {
  try {
    classes.value = await getClasses()
    if (classes.value.length > 0) {
      const first = classes.value[0]
      selectedClass.value = first.name
      selectedClassId.value = first.id
      availableSubjects.value = first.subjects || ['语文', '数学', '英语']
      await loadData()
    }
  } catch (error) {
    showFailToast('加载班级失败')
  }
}

// 加载数据
const loadData = async () => {
  if (!selectedClassId.value) return
  
  // 加载学习小组
  try {
    studyGroups.value = await getStudyGroups(selectedClassId.value)
  } catch {
    studyGroups.value = []
  }
  
  // 加载学生
  try {
    const res = await getStudents({ class_id: selectedClassId.value })
    let studentsList = res.items
    // 根据组别筛选
    if (selectedGroupId.value) {
      studentsList = studentsList.filter(s => s.study_group_id === selectedGroupId.value)
    }
    students.value = studentsList
  } catch (error) {
    showFailToast('加载学生失败')
  }
  
  // 加载评价维度
  try {
    dimensions.value = await getDimensions(selectedClassId.value)
    // 根据科目筛选
    if (selectedSubject.value) {
      dimensions.value = dimensions.value.filter(d => d.subject === selectedSubject.value)
    }
    if (dimensions.value.length > 0) {
      selectedDimensionId.value = dimensions.value[0].id
    } else {
      selectedDimensionId.value = ''
    }
  } catch (error) {
    showFailToast('加载评价维度失败')
  }
}

// 加载已有评价
const loadExistingEvaluations = async () => {
  if (!selectedClassId.value || !selectedDimensionId.value) return
  
  try {
    const res = await getEvaluations({
      class_id: selectedClassId.value,
      dimension_id: selectedDimensionId.value,
      start_date: selectedDate.value,
      end_date: selectedDate.value
    })
    
    // 填充已有评价
    Object.keys(evaluations).forEach(key => delete evaluations[key])
    res.forEach((e: any) => {
      evaluations[e.student_id] = e.value
    })
  } catch (error) {
    // 忽略
  }
}

// 监听维度变化，重新加载评价
watch([selectedDimensionId, selectedDate], () => {
  loadExistingEvaluations()
})

import StarInput from '@/components/evaluation/StarInput.vue'
import GradeInput from '@/components/evaluation/GradeInput.vue'
import ScoreInput from '@/components/evaluation/ScoreInput.vue'
import ABScoreInput from '@/components/evaluation/ABScoreInput.vue'
import BooleanInput from '@/components/evaluation/BooleanInput.vue'
import TextInput from '@/components/evaluation/TextInput.vue'

// 获取小组名称
const getGroupName = (groupId: string) => {
  const group = studyGroups.value.find(g => g.id === groupId)
  return group?.name || ''
}

// 保存单个评价
const saveSingle = async (studentId: string) => {
  const value = evaluations[studentId]
  if (!value) return
  
  try {
    await saveEvaluation({
      dimension_id: selectedDimensionId.value,
      student_id: studentId,
      record_date: selectedDate.value,
      value: String(value)
    })
    showSuccessToast('保存成功')
  } catch (error) {
    showFailToast('保存失败')
  }
}

// 批量保存
const saveAll = async () => {
  const records = Object.entries(evaluations)
    .filter(([_, value]) => value)
    .map(([studentId, value]) => ({
      dimension_id: selectedDimensionId.value,
      student_id: studentId,
      record_date: selectedDate.value,
      value: String(value)
    }))
  
  if (records.length === 0) {
    showFailToast('请至少填写一条评价')
    return
  }
  
  saving.value = true
  try {
    await saveBatchEvaluations(records)
    showSuccessToast(`已保存${records.length}条评价`)
  } catch (error) {
    showFailToast('保存失败')
  } finally {
    saving.value = false
  }
}

// 应用快捷评语
const applyTemplate = (tpl: string) => {
  if (currentDimension.value?.type === 'text') {
    students.value.forEach(s => {
      if (!evaluations[s.id]) {
        evaluations[s.id] = tpl
      }
    })
  }
}

// 批量赋值
const batchValue = ref('')
const doBatchAssign = () => {
  if (!batchValue.value) return
  students.value.forEach(s => {
    evaluations[s.id] = batchValue.value
  })
  showBatchAssign.value = false
  showSuccessToast(`已为${students.value.length}名学生设置相同值`)
}

// 键盘导航：Tab键切换学生
const handleKeyDown = (event: KeyboardEvent, index: number) => {
  if (event.key === 'Tab' && !event.shiftKey) {
    event.preventDefault()
    const nextIndex = index + 1
    if (nextIndex < students.value.length) {
      focusedIndex.value = nextIndex
      rowRefs.value[nextIndex]?.focus()
    }
  } else if (event.key === 'Tab' && event.shiftKey) {
    event.preventDefault()
    const prevIndex = index - 1
    if (prevIndex >= 0) {
      focusedIndex.value = prevIndex
      rowRefs.value[prevIndex]?.focus()
    }
  } else if (event.key === 'Enter') {
    // Enter保存当前学生
    const student = students.value[index]
    if (evaluations[student.id]) {
      saveSingle(student.id)
      // 自动跳转到下一个
      const nextIndex = index + 1
      if (nextIndex < students.value.length) {
        focusedIndex.value = nextIndex
        rowRefs.value[nextIndex]?.focus()
      }
    }
  }
}

// 复制前一天数据
const copyFromYesterday = async () => {
  if (!selectedClassId.value || !selectedDimensionId.value) return
  
  // 计算前一天日期
  const date = new Date(selectedDate.value)
  date.setDate(date.getDate() - 1)
  const yesterday = date.toISOString().split('T')[0]
  
  copying.value = true
  try {
    const res = await getEvaluations({
      class_id: selectedClassId.value,
      dimension_id: selectedDimensionId.value,
      start_date: yesterday,
      end_date: yesterday
    })
    
    if (res.length === 0) {
      showFailToast('前一天没有评价数据')
      return
    }
    
    // 复制数据（仅覆盖未填写的）
    let copied = 0
    res.forEach((e: any) => {
      if (!evaluations[e.student_id]) {
        evaluations[e.student_id] = e.value
        copied++
      }
    })
    
    showSuccessToast(`已复制${copied}条评价`)
  } catch (error) {
    showFailToast('复制失败')
  } finally {
    copying.value = false
  }
}

// 日期确认
const onDateConfirm = ({ selectedValues }: any) => {
  selectedDate.value = selectedValues.join('-')
  showDatePicker.value = false
  loadExistingEvaluations()
}

// 班级确认
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClass.value = selected.text
  selectedClassId.value = selected.value
  showClassPicker.value = false
  
  // 更新科目和组别
  const cls = classes.value.find(c => c.id === selectedClassId.value)
  availableSubjects.value = cls?.subjects || ['语文', '数学', '英语']
  selectedSubject.value = ''
  selectedGroupId.value = ''
  selectedGroupLabel.value = ''
  
  loadData()
}

// 科目确认
const onSubjectConfirm = ({ selectedOptions }: any) => {
  selectedSubject.value = selectedOptions[0].value
  showSubjectPicker.value = false
  loadData()
}

// 组别确认
const onGroupConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedGroupId.value = selected.value
  selectedGroupLabel.value = selected.text
  showGroupPicker.value = false
  loadData()
}

// 初始化
onMounted(() => {
  const today = new Date()
  datePickerValue.value = [
    String(today.getFullYear()),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0')
  ]
  loadClasses()
})
</script>

<style scoped lang="scss">
.evaluation-grid {
  padding: 12px;
  padding-bottom: 80px;
  
  .header-section {
    margin-bottom: 12px;
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .dimension-section {
    padding: 12px;
    
    :deep(.van-radio-group) {
      flex-wrap: wrap;
      gap: 8px;
    }
  }
  
  .grid-container {
    .grid-header {
      display: flex;
      padding: 12px;
      font-weight: 500;
      background: #f7f8fa;
      
      .grid-cell {
        text-align: center;
        
        &.student-cell {
          flex: 1;
          text-align: left;
        }
        
        &.rating-cell {
          width: 150px;
        }
        
        &.action-cell {
          width: 80px;
        }
      }
    }
    
    .grid-row {
      display: flex;
      padding: 12px;
      border-bottom: 1px solid #ebedf0;
      align-items: center;
      
      &.has-value {
        background: #f0f9ff;
      }
      
      .grid-cell {
        &.student-cell {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
          
          .student-name {
            font-size: 14px;
          }
        }
        
        &.rating-cell {
          width: 150px;
          display: flex;
          justify-content: center;
        }
        
        &.action-cell {
          width: 80px;
          display: flex;
          justify-content: center;
        }
      }
    }
    
    .batch-actions {
      padding: 16px;
    }
  }
  
  .templates-section {
    padding: 12px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    
    .template-tag {
      cursor: pointer;
    }
  }
}
</style>
