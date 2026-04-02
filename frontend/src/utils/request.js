import axios from 'axios'

const request = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/',
  timeout: 5000
})

// 请求拦截
request.interceptors.request.use(config => {
  return config
})

// 响应拦截
request.interceptors.response.use(res => {
  return res.data
})

export default request