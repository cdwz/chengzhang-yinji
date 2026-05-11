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
            <component
              :is="getRatingComponent()"
              v-model="evaluations[student.id]"
              v-bind="getRatingProps()"
            />
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { showSuccessToast, showFailToast } from 'vant'
import { getClasses } from '@/api/schools'
import { getStudents } from '@/api/students'
import { getDimensions, getEvaluations, saveEvaluation, saveBatchEvaluations } from '@/api/evaluations'
import type { Class, Student, EvaluationDimension } from '@/api/types'

// 状态
const classes = ref<Class[]>([])
const students = ref<Student[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const evaluations = reactive<Record<string, any>>({})
const saving = ref(false)
const copying = ref(false)

// 键盘导航
const rowRefs = ref<HTMLElement[]>([])
const focusedIndex = ref(-1)

// 选择
const selectedDate = ref(new Date().toISOString().split('T')[0])
const selectedClass = ref('')
const selectedClassId = ref('')
const selectedDimensionId = ref('')
const showDatePicker = ref(false)
const showClassPicker = ref(false)
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
      await loadData()
    }
  } catch (error) {
    showFailToast('加载班级失败')
  }
}

// 加载数据
const loadData = async () => {
  if (!selectedClassId.value) return
  
  // 加载学生
  try {
    const res = await getStudents({ class_id: selectedClassId.value })
    students.value = res.items
  } catch (error) {
    showFailToast('加载学生失败')
  }
  
  // 加载评价维度
  try {
    dimensions.value = await getDimensions(selectedClassId.value)
    if (dimensions.value.length > 0) {
      selectedDimensionId.value = dimensions.value[0].id
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

// 获取评分组件
const getRatingComponent = () => {
  const type = currentDimension.value?.type
  switch (type) {
    case 'star':
      return 'van-rate'
    case 'boolean':
      return 'van-switch'
    case 'score':
      return 'van-stepper'
    default:
      return 'van-field'
  }
}

// 获取评分组件属性
const getRatingProps = () => {
  const type = currentDimension.value?.type
  switch (type) {
    case 'star':
      return { count: 5, size: 20 }
    case 'boolean':
      return { size: 20 }
    case 'score':
      return { min: 0, max: 100, step: 5 }
    default:
      return { placeholder: '输入评语', autosize: true }
  }
}

// 获取小组名称
const getGroupName = (_groupId: string) => {
  // TODO: 从小组列表中获取名称
  return ''
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
    // 为所有未填写的应用
    students.value.forEach(s => {
      if (!evaluations[s.id]) {
        evaluations[s.id] = tpl
      }
    })
  }
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
