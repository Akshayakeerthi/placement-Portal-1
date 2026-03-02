import api from '../services/api.js';

export default {
  props: ['onAuth'],
  data() {
    return {
      isRegister: false,
      form: { name: '', email: '', password: '', role: 'STUDENT' },
      error: '',
    };
  },
  methods: {
    async submit() {
      this.error = '';
      try {
        if (this.isRegister) {
          await api.post('/auth/register', this.form);
        }
        const res = await api.post('/auth/login', {
          email: this.form.email,
          password: this.form.password,
        });
        localStorage.setItem('token', res.data.token);
        localStorage.setItem('role', res.data.role);
        this.onAuth(res.data.role);
      } catch (e) {
        this.error = e.response?.data?.error || 'Authentication failed';
      }
    },
  },
  template: `
    <div class="row justify-content-center">
      <div class="col-md-6 card p-4 shadow-sm">
        <h4 class="mb-3">{{ isRegister ? 'Register' : 'Login' }}</h4>
        <div v-if="isRegister" class="mb-2"><input v-model="form.name" class="form-control" placeholder="Name"></div>
        <div class="mb-2"><input v-model="form.email" class="form-control" placeholder="Email"></div>
        <div class="mb-2"><input v-model="form.password" type="password" class="form-control" placeholder="Password"></div>
        <div v-if="isRegister" class="mb-3">
          <select v-model="form.role" class="form-select">
            <option value="STUDENT">Student</option>
            <option value="COMPANY">Company</option>
          </select>
        </div>
        <button class="btn btn-primary w-100" @click="submit">{{ isRegister ? 'Register & Login' : 'Login' }}</button>
        <button class="btn btn-link mt-2" @click="isRegister = !isRegister">Switch to {{ isRegister ? 'Login' : 'Register' }}</button>
        <div class="text-danger mt-2">{{ error }}</div>
      </div>
    </div>
  `,
};
