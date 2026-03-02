import api from '../services/api.js';

export default {
  emits: ['logged-in'],
  data() {
    return {
      mode: 'login',
      form: { name: '', email: '', password: '', role: 'STUDENT' },
      loading: false,
      error: '',
    };
  },
  methods: {
    async submit() {
      this.error = '';
      this.loading = true;
      try {
        if (this.mode === 'register') {
          await api.post('/auth/register', this.form);
        }
        const res = await api.post('/auth/login', { email: this.form.email, password: this.form.password });
        localStorage.setItem('token', res.data.token);
        localStorage.setItem('role', res.data.role);
        localStorage.setItem('name', res.data.name);
        this.$emit('logged-in', res.data.role);
      } catch (e) {
        this.error = e.response?.data?.error || 'Authentication failed';
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
    <div class="row justify-content-center">
      <div class="col-lg-6 card shadow-sm p-4">
        <h4 class="mb-3">{{ mode === 'login' ? 'Login' : 'Register' }}</h4>
        <div class="mb-2" v-if="mode==='register'"><input class="form-control" v-model="form.name" placeholder="Name" /></div>
        <div class="mb-2"><input class="form-control" v-model="form.email" placeholder="Email" /></div>
        <div class="mb-2"><input class="form-control" type="password" v-model="form.password" placeholder="Password" /></div>
        <div class="mb-3" v-if="mode==='register'">
          <select class="form-select" v-model="form.role">
            <option value="STUDENT">Student</option>
            <option value="COMPANY">Company</option>
          </select>
        </div>
        <button :disabled="loading" class="btn btn-primary w-100" @click="submit">{{ loading ? 'Please wait...' : (mode==='login' ? 'Login' : 'Register & Login') }}</button>
        <button class="btn btn-link mt-2" @click="mode = (mode==='login' ? 'register':'login')">Switch to {{ mode==='login' ? 'Register' : 'Login' }}</button>
        <div class="text-danger">{{ error }}</div>
      </div>
    </div>
  `,
};
