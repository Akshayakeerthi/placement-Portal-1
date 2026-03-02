import api from '../services/api.js';

export default {
  data() {
    return {
      profile: { company_name: '', website: '', description: '' },
      drive: { title: '', description: '', eligible_branches: '', min_cgpa: 6, graduation_year: 2025, deadline: '' },
      msg: '',
    };
  },
  methods: {
    async saveProfile() {
      await api.post('/company/profile', this.profile);
      this.msg = 'Profile submitted for approval';
    },
    async createDrive() {
      const payload = { ...this.drive, eligible_branches: this.drive.eligible_branches.split(',').map((v) => v.trim()) };
      await api.post('/company/drives', payload);
      this.msg = 'Drive submitted for approval';
    },
  },
  template: `
  <div>
    <h3>Company Dashboard</h3>
    <div class="card p-3 mb-3">
      <h5>Company Profile</h5>
      <input class="form-control mb-2" v-model="profile.company_name" placeholder="Company Name"/>
      <input class="form-control mb-2" v-model="profile.website" placeholder="Website"/>
      <textarea class="form-control mb-2" v-model="profile.description" placeholder="Description"></textarea>
      <button class="btn btn-primary" @click="saveProfile">Save Profile</button>
    </div>
    <div class="card p-3">
      <h5>Create Drive</h5>
      <input class="form-control mb-2" v-model="drive.title" placeholder="Title"/>
      <textarea class="form-control mb-2" v-model="drive.description" placeholder="Description"></textarea>
      <input class="form-control mb-2" v-model="drive.eligible_branches" placeholder="Eligible Branches CSV"/>
      <input class="form-control mb-2" type="number" v-model="drive.min_cgpa" placeholder="Min CGPA"/>
      <input class="form-control mb-2" type="number" v-model="drive.graduation_year" placeholder="Graduation Year"/>
      <input class="form-control mb-2" type="datetime-local" v-model="drive.deadline"/>
      <button class="btn btn-success" @click="createDrive">Submit Drive</button>
    </div>
    <div class="text-success mt-2">{{msg}}</div>
  </div>
  `,
};
