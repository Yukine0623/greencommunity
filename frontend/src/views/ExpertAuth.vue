<template>
  <div class="auth-container">
    <h2>申请成为专业服务者</h2>
    <div class="form-card">
      <div class="form-group">
        <label>真实姓名</label>
        <input v-model="form.real_name" placeholder="请输入身份证姓名" />
      </div>
      <div class="form-group">
        <label>身份证号</label>
        <input v-model="form.id_card" placeholder="请输入18位身份证号" />
      </div>
      <div class="form-group">
        <label>擅长技能</label>
        <textarea v-model="form.skills" placeholder="描述您的专业能力"></textarea>
      </div>
      <div class="form-group">
        <label>资质证明（证书/身份证照片）</label>
        <div class="upload-area" @click="$refs.fileInput.click()">
          <span v-if="!imagePreview">点击上传图片</span>
          <img v-else :src="imagePreview" class="preview-img" />
          <input type="file" ref="fileInput" hidden @change="handleFileUpload" accept="image/*" />
        </div>
      </div>
      <BaseButton @click="submitAuth" :loading="submitting" type="primary">提交申请</BaseButton>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useUserStore } from '../store/user';
import request from '../utils/request';

const form = ref({ real_name: '', id_card: '', skills: '', certificate: null });
const imagePreview = ref(null);
const submitting = ref(false);

const handleFileUpload = (e) => {
  const file = e.target.files[0];
  if (file) {
    form.value.certificate = file;
    imagePreview.value = URL.createObjectURL(file);
  }
};

const submitAuth = async () => {
  const formData = new FormData();
  formData.append('real_name', form.value.real_name);
  formData.append('id_card', form.value.id_card);
  formData.append('skills', form.value.skills);
  formData.append('certificate', form.value.certificate);

  submitting.value = true;
  try {
    await request.post('/api/users/expert-apply/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    alert('提交成功！');
  } catch (error) {
    alert(error.response?.data?.detail || '提交失败');
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
/* 利用你擅长的CSS进行美化 */
.upload-area {
  border: 2px dashed #ddd;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  border-radius: 8px;
  margin-top: 10px;
}
.preview-img { max-width: 100%; max-height: 200px; }
</style>