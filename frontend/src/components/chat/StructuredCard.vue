<template>
  <div class="structured-card" :class="type">
    <div class="card-header">
      <span class="icon">{{ iconMap[type] || '📋' }}</span>
      <span class="title">{{ titleMap[type] || '数据' }}</span>
    </div>

    <div class="card-body">
      <!-- 天气卡片 -->
      <template v-if="type === 'weather'">
        <div class="weather-card">
          <div class="weather-main">
            <span class="temp">{{ data.temperature }}°C</span>
            <span class="weather-icon">{{ getWeatherIcon(data.weather) }}</span>
          </div>
          <div class="weather-info">
            <div class="info-item">
              <span class="label">城市</span>
              <span class="value">{{ data.city }}</span>
            </div>
            <div class="info-item">
              <span class="label">天气</span>
              <span class="value">{{ data.weather }}</span>
            </div>
            <div class="info-item">
              <span class="label">风力</span>
              <span class="value">{{ data.wind }}</span>
            </div>
            <div v-if="data.air_quality" class="info-item">
              <span class="label">空气质量</span>
              <span class="value">{{ data.air_quality.level }}</span>
            </div>
          </div>
          <div v-if="data.suggestion" class="suggestion">
            💡 {{ data.suggestion }}
          </div>
        </div>
      </template>

      <!-- 火车票卡片 -->
      <template v-else-if="type === 'train'">
        <div class="train-card">
          <div class="route">
            <span class="city">{{ data.origin }}</span>
            <span class="arrow">→</span>
            <span class="city">{{ data.destination }}</span>
          </div>
          <div class="date">📅 {{ data.date }}</div>
          <div class="train-list">
            <div 
              v-for="train in (data.trains || []).slice(0, 3)" 
              :key="train.train_no"
              class="train-item"
            >
              <div class="train-no">{{ train.train_no }}</div>
              <div class="train-time">
                {{ train.departure_time }} - {{ train.arrival_time }}
              </div>
              <div class="train-duration">{{ train.duration }}</div>
            </div>
          </div>
          <div class="total">共 {{ data.total }} 个车次</div>
        </div>
      </template>

      <!-- 知识卡片 -->
      <template v-else-if="type === 'knowledge'">
        <div class="knowledge-card">
          <div class="query">🔍 {{ data.query }}</div>
          <div class="sources">
            <el-tag v-for="s in data.sources" :key="s" size="small">
              {{ s }}
            </el-tag>
          </div>
        </div>
      </template>

      <!-- 默认 JSON 展示 -->
      <template v-else>
        <pre class="json-view">{{ JSON.stringify(data, null, 2) }}</pre>
      </template>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  type: {
    type: String,
    required: true,
  },
  data: {
    type: Object,
    required: true,
  },
})

const iconMap = {
  weather: '🌤️',
  train: '🚄',
  knowledge: '📚',
}

const titleMap = {
  weather: '天气信息',
  train: '火车票信息',
  knowledge: '知识检索',
}

function getWeatherIcon(weather) {
  const icons = {
    '晴': '☀️',
    '多云': '⛅',
    '阴': '☁️',
    '雨': '🌧️',
    '雪': '❄️',
    '雷': '⛈️',
  }
  for (const [key, icon] of Object.entries(icons)) {
    if (weather?.includes(key)) return icon
  }
  return '🌡️'
}
</script>

<style lang="scss" scoped>
.structured-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  
  &.weather {
    border-color: #409eff;
    .card-header { background: #ecf5ff; color: #409eff; }
  }
  
  &.train {
    border-color: #67c23a;
    .card-header { background: #f0f9eb; color: #67c23a; }
  }
  
  &.knowledge {
    border-color: #e6a23c;
    .card-header { background: #fdf6ec; color: #e6a23c; }
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-weight: 500;
  font-size: 13px;
  
  .icon {
    font-size: 16px;
  }
}

.card-body {
  padding: 12px;
}

// 天气卡片
.weather-card {
  .weather-main {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin-bottom: 12px;
    
    .temp {
      font-size: 36px;
      font-weight: 600;
      color: var(--text-primary);
    }
    
    .weather-icon {
      font-size: 40px;
    }
  }
  
  .weather-info {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    
    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 4px 8px;
      background: #f5f7fa;
      border-radius: 4px;
      font-size: 12px;
      
      .label {
        color: var(--text-secondary);
      }
      
      .value {
        font-weight: 500;
      }
    }
  }
  
  .suggestion {
    margin-top: 12px;
    padding: 8px;
    background: #f0f9eb;
    border-radius: 6px;
    font-size: 12px;
    color: #67c23a;
  }
}

// 火车票卡片
.train-card {
  .route {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 8px;
    
    .arrow {
      color: var(--text-secondary);
    }
  }
  
  .date {
    text-align: center;
    color: var(--text-secondary);
    font-size: 13px;
    margin-bottom: 12px;
  }
  
  .train-list {
    .train-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px;
      background: #f5f7fa;
      border-radius: 6px;
      margin-bottom: 6px;
      font-size: 13px;
      
      .train-no {
        font-weight: 600;
        color: #409eff;
      }
      
      .train-duration {
        color: var(--text-secondary);
      }
    }
  }
  
  .total {
    text-align: center;
    color: var(--text-secondary);
    font-size: 12px;
    margin-top: 8px;
  }
}

// 知识卡片
.knowledge-card {
  .query {
    margin-bottom: 8px;
    font-weight: 500;
  }
  
  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }
}

// JSON 预览
.json-view {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 200px;
}
</style>
