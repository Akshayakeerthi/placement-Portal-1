import api from '../services/api.js';

export default {
  emits: ['logged-in'],
  data() {
    return {
      mode: 'login',
      form: { name: '', email: '', password: '', confirm_password: '', role: 'STUDENT' },
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
          if (this.form.password !== this.form.confirm_password) {
            throw new Error('Password and confirm password must match');
          }
          await api.post('/auth/register', this.form);
        }
        const res = await api.post('/auth/login', { email: this.form.email, password: this.form.password });
        localStorage.setItem('token', res.data.token);
        localStorage.setItem('role', res.data.role);
        localStorage.setItem('name', res.data.name);
        this.$emit('logged-in', res.data.role);
      } catch (e) {
        this.error = e.response?.data?.error || e.message || 'Authentication failed';
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
    <div class="row justify-content-center">
      <div class="col-lg-6">
        <div class="glass-card p-4">
          <h4 class="section-title mb-2">{{ mode === 'login' ? 'Login to Your Account' : 'Create an Account' }}</h4>
          <p class="text-muted mb-3">Access opportunities, manage drives, and track placements in one place.</p>

          <div class="mb-2" v-if="mode==='register'">
            <label class="form-label">Full Name</label>
            <input class="form-control" v-model="form.name" placeholder="Enter your name" />
          </div>
          <div class="mb-2">
            <label class="form-label">Email</label>
            <input class="form-control" v-model="form.email" placeholder="Enter email" />
          </div>
          <div class="mb-2">
            <label class="form-label">Password</label>
            <input class="form-control" type="password" v-model="form.password" placeholder="Enter password" />
          </div>
          <div class="mb-2" v-if="mode==='register'">
            <label class="form-label">Re-enter Password</label>
            <input class="form-control" type="password" v-model="form.confirm_password" placeholder="Re-enter password" />
          </div>
          <div class="mb-3" v-if="mode==='register'">
            <label class="form-label">Role</label>
            <select class="form-select" v-model="form.role">
              <option value="STUDENT">Student</option>
              <option value="COMPANY">Company</option>
            </select>
          </div>

          <button :disabled="loading" class="btn btn-primary w-100" @click="submit">{{ loading ? 'Please wait...' : (mode==='login' ? 'Login' : 'Register & Login') }}</button>
          <button class="btn btn-link mt-2" @click="mode = (mode==='login' ? 'register':'login')">Switch to {{ mode==='login' ? 'Register' : 'Login' }}</button>
          <div class="alert alert-danger py-2 mt-2 mb-0" v-if="error">{{ error }}</div>
        </div>
      </div>
    </div>
  `,
};
