<template>
  <div class="growth-index">
    <van-cell-group inset>
      <van-cell title="我的成长" />
      
      <div class="growth-stats">
        <div class="stat-item">
          <div class="stat-value">12</div>
          <div class="stat-label">连续坚持天数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">85%</div>
          <div class="stat-label">本周完成率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">4</div>
          <div class="stat-label">获得成就</div>
        </div>
      </div>
    </van-cell-group>
    
    <van-cell-group inset style="margin-top: 16px;">
      <van-cell title="班级分布概况" />
      <div class="anonymous-stats">
        <p class="hint">以下数据为匿名统计，不显示其他同学信息</p>
        <div class="stats-chart">
          <div class="stats-item">
            <span class="label">约40%的同学</span>
            <span class="value">获得5星评价</span>
          </div>
          <div class="stats-item">
            <span class="label">约35%的同学</span>
            <span class="value">获得4星评价</span>
          </div>
        </div>
      </div>
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
// 成长档案页面
</script>

<style scoped lang="scss">
.growth-index {
  .growth-stats {
    display: flex;
    padding: 16px;
    
    .stat-item {
      flex: 1;
      text-align: center;
      
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #409eff;
      }
      
      .stat-label {
        font-size: 12px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }
  
  .anonymous-stats {
    padding: 16px;
    
    .hint {
      font-size: 12px;
      color: #909399;
      margin-bottom: 12px;
    }
    
    .stats-chart {
      .stats-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #f0f0f0;
        
        &:last-child {
          border-bottom: none;
        }
        
        .label {
          color: #606266;
        }
        
        .value {
          color: #303133;
          font-weight: 500;
        }
      }
    }
  }
}
</style>
