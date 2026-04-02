import request from '@/utils/request'

// 获取帖子
export const getPosts = (username) => {
  return request.get('posts/', {
    params: { username }
  })
}

// 发帖
export const createPost = (data) => {
  return request.post('create_post/', data)
}