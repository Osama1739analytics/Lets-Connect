
content = """{% extends 'base.html' %}

{% block title %}{{ title }} - Let's Connect{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <!-- Widen the form container to col-lg-10 as requested -->
        <div class="col-lg-10">
            <div class="card border-0 shadow-lg" style="background: rgba(255, 255, 255, 0.95); border-radius: 24px;">
                <div class="card-body p-5">
                    <h2 class="text-center fw-bold text-dark mb-2">{{ title }}</h2>
                    <p class="text-center text-muted mb-5">Fill in the details below to get started.</p>

                    <form method="post" id="sessionForm">
                        {% csrf_token %}

                        <!-- Nature Selection (Icon Cards) -->
                        <div class="mb-5">
                            <label class="form-label fw-bold h5 mb-3 text-dark">What kind of session is this? <span
                                    class="text-danger">*</span></label>
                            <div class="row g-3 row-cols-1 row-cols-md-3">
                                <!-- Option 1: Course Guidance -->
                                <div class="col">
                                    <input type="radio" class="btn-check" name="nature" id="nature_course"
                                        value="course" {% if form.nature.value == 'course' %} checked {% endif %}
                                        required>
                                    <label
                                        class="btn btn-outline-light text-dark h-100 w-100 p-4 border shadow-sm nature-card"
                                        for="nature_course">
                                        <i class="fas fa-graduation-cap fa-3x mb-3 text-primary"></i>
                                        <div class="fw-bold">Course</div>
                                        <div class="small text-muted">Guidance</div>
                                    </label>
                                </div>
                                <!-- Option 2: Career Advice -->
                                <div class="col">
                                    <input type="radio" class="btn-check" name="nature" id="nature_career"
                                        value="career" {% if form.nature.value == 'career' %} checked {% endif %}>
                                    <label
                                        class="btn btn-outline-light text-dark h-100 w-100 p-4 border shadow-sm nature-card"
                                        for="nature_career">
                                        <i class="fas fa-briefcase fa-3x mb-3 text-success"></i>
                                        <div class="fw-bold">Career</div>
                                        <div class="small text-muted">Advice</div>
                                    </label>
                                </div>
                                <!-- Option 3: General Topic -->
                                <div class="col">
                                    <input type="radio" class="btn-check" name="nature" id="nature_topic" value="topic"
                                        {% if form.nature.value == 'topic' %} checked {% endif %}>
                                    <label
                                        class="btn btn-outline-light text-dark h-100 w-100 p-4 border shadow-sm nature-card"
                                        for="nature_topic">
                                        <i class="fas fa-comments fa-3x mb-3 text-warning"></i>
                                        <div class="fw-bold">General</div>
                                        <div class="small text-muted">Topic</div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <!-- Topic / Subject -->
                        <div class="mb-4">
                            <label for="id_subject_detail" class="form-label fw-bold">Topic / Subject <span
                                    class="text-danger">*</span></label>
                            <input type="text" name="subject_detail" class="form-control"
                                placeholder="Enter Name (Course/Career/Topic)" id="id_subject_detail" required
                                value="{{ form.subject_detail.value|default:'' }}">
                        </div>

                        <!-- Description -->
                        <div class="mb-4">
                            <label for="id_description" class="form-label fw-bold">Description <span
                                    class="text-danger">*</span></label>
                            <textarea name="description" cols="40" rows="3" class="form-control"
                                placeholder="Describe what you want to learn or teach..." id="id_description"
                                required>{{ form.description.value|default:'' }}</textarea>
                        </div>

                        <!-- Date & Time (Split Inputs) -->
                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label for="date_input" class="form-label fw-bold">Preferred Date <span
                                        class="text-danger">*</span></label>
                                <div class="input-group">
                                    <span class="input-group-text bg-white border-end-0"><i
                                            class="far fa-calendar-alt text-primary"></i></span>
                                    <input type="date" id="date_input" class="form-control border-start-0 ps-0"
                                        required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label for="time_input" class="form-label fw-bold">Preferred Time <span
                                        class="text-danger">*</span></label>
                                <div class="input-group">
                                    <span class="input-group-text bg-white border-end-0"><i
                                            class="far fa-clock text-primary"></i></span>
                                    <input type="time" id="time_input" class="form-control border-start-0 ps-0"
                                        required>
                                </div>
                            </div>
                        </div>

                        <!-- Hidden Scheduled At Field (Synced via JS) -->
                        <input type="hidden" name="scheduled_at" id="id_scheduled_at"
                            value="{{ form.scheduled_at.value|date:'Y-m-d\\TH:i'|default:'' }}">

                        <!-- Flexibility -->
                        <div class="mb-5">
                            <label for="id_flexibility_comments" class="form-label fw-bold">Flexibility / Comments <span
                                    class="text-muted fw-normal">(Optional)</span></label>
                            <textarea name="flexibility_comments" cols="40" rows="2" class="form-control"
                                placeholder="e.g. Can start 30 mins before or after"
                                id="id_flexibility_comments">{{ form.flexibility_comments.value|default:'' }}</textarea>
                        </div>

                        <!-- Submit Button -->
                        <div class="mt-4">
                            <button type="submit"
                                class="btn btn-primary btn-lg w-100 rounded-pill fw-bold shadow-sm py-3">
                                {% if request.user.user_type == 'mentee' %}
                                {% if form.instance.pk %}Update Request{% else %}Request Session{% endif %}
                                {% else %}
                                {% if form.instance.pk %}Update Post{% else %}Post Session{% endif %}
                                {% endif %}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    /* Card Selection Styling */
    .nature-card {
        transition: all 0.3s ease;
        border: 2px solid transparent !important;
        background-color: #f8f9fa;
    }

    .btn-check:checked+.nature-card {
        background-color: white;
        border-color: var(--primary-color) !important;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(42, 93, 132, 0.15) !important;
    }

    .btn-check:checked+.nature-card i {
        transform: scale(1.1);
        transition: transform 0.3s ease;
    }

    /* Form Control Styling */
    .form-control,
    .form-select {
        border-radius: 12px;
        padding: 0.75rem 1rem;
        border: 1px solid #e2e8f0;
        background-color: #f8f9fa;
    }

    .form-control:focus {
        background-color: white;
        box-shadow: 0 0 0 4px rgba(42, 93, 132, 0.1);
        border-color: var(--primary-color);
    }

    .input-group-text {
        border-radius: 12px 0 0 12px;
        border: 1px solid #e2e8f0;
    }
</style>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        // Sync Date/Time inputs to the hidden scheduled_at field
        const dateInput = document.getElementById('date_input');
        const timeInput = document.getElementById('time_input');
        const hiddenInput = document.getElementById('id_scheduled_at');
        const form = document.getElementById('sessionForm');

        function updateDateTime() {
            if (dateInput.value && timeInput.value) {
                hiddenInput.value = `${dateInput.value}T${timeInput.value}`;
            }
        }

        dateInput.addEventListener('change', updateDateTime);
        timeInput.addEventListener('change', updateDateTime);

        // Pre-fill if editing (populate Date/Time from hidden value)
        const currentVal = hiddenInput.value;
        if (currentVal) {
            // value format: YYYY-MM-DDTHH:MM
            const parts = currentVal.split('T');
            if (parts.length === 2) {
                dateInput.value = parts[0];
                timeInput.value = parts[1]; // HH:MM
            }
        }

        // Manual validation on submit
        form.addEventListener('submit', function (e) {
            if (!dateInput.value || !timeInput.value) {
                e.preventDefault();
                alert('Please select both a date and a time.');
            } else {
                updateDateTime();
            }
        });
    });
</script>
{% endblock %}
"""

with open(r"c:\Users\Shary\Desktop\FYP - P2P\Peer2ProfessionalGuidanceApp\Peer-2-Professional Guidance App\templates\session_form_v2.html", "w", encoding='utf-8') as f:
    f.write(content)
