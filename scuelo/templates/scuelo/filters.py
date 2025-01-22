{% extends "../layout.html" %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb">
        <ol class="breadcrumb">
            {% for url, name in breadcrumbs %}
                <li class="breadcrumb-item {% if forloop.last %}active{% endif %}">
                    {% if not forloop.last %}
                        <a href="{{ url }}">{{ name }}</a>
                    {% else %}
                        {{ name }}
                    {% endif %}
                </li>
            {% endfor %}
        </ol>
    </nav>

    <!-- Main Content Layout -->
    <div class="main-layout">
        <!-- Quick Access Section -->
        <div class="panel">
            <h3 class="panel-title">Quick Access</h3>
            <div class="quick-access-grid">
                <a href="{% url 'new_student' %}" class="btn btn-primary quick-btn">New Student</a>
                <a href="{% url 'mouvement_list' %}" class="btn btn-info quick-btn">Movements</a>
                {% comment %}
                    <a href="{% url 'cash_flow_report' %}" class="btn btn-success quick-btn">Cash Flow</a>
                {% endcomment %}
                <a href="{% url 'uniform_payments' %}" class="btn btn-warning quick-btn">Uniforms</a>
                <a href="{% url 'uniform-reservation-list' %}" class="btn btn-warning quick-btn">Uniforms reservation</a>

                <a href="{% url 'late_payment_report' %}" class="btn btn-danger quick-btn">Late Payments</a>
                <a href="{% url 'school_management' %}" class="btn btn-secondary quick-btn">Schools</a>
                <a href="{% url 'user_list' %}" class="btn btn-dark quick-btn">Users</a>
                <a href="{% url 'annee_scolaire_manage' %}" class="btn btn-outline-secondary quick-btn">
                    Manage Année Scolaire
                </a>
                <a href="{% url 'offsite_students' %}" class="btn btn-outline-primary quick-btn">Off-site Students</a>
            </div>
        </div>

        <!-- Class List Section -->
        <div class="panel">
            <h3 class="panel-title">Classes</h3>
            <div class="school-grid">
                {% for school, categories in data.items %}
                    <div class="school-section">
                        <h4 class="school-title">{{ school.nom }}</h4>

                        <!-- Display each category only if it contains classes -->
                        {% if categories.Maternelle %}
                            <div class="category-section">
                                <h5 class="category-title">Maternelle</h5>
                                <div class="class-grid">
                                    {% for item in categories.Maternelle %}
                                        <a href="{% url 'class_detail' item.classe.id %}" class="class-card">
                                            <i class="fas fa-{{ item.icon }} class-icon"></i>
                                            <span>{{ item.classe.nom }}</span>
                                        </a>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endif %}

                        {% if categories.Primaire %}
                            <div class="category-section">
                                <h5 class="category-title">Primaire</h5>
                                <div class="class-grid">
                                    {% for item in categories.Primaire %}
                                        <a href="{% url 'class_detail' item.classe.id %}" class="class-card">
                                            <i class="fas fa-{{ item.icon }} class-icon"></i>
                                            <span>{{ item.classe.nom }}</span>
                                        </a>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endif %}

                        {% if categories.Secondaire %}
                            <div class="category-section">
                                <h5 class="category-title">Secondaire</h5>
                                <div class="class-grid">
                                    {% for item in categories.Secondaire %}
                                        <a href="{% url 'class_detail' item.classe.id %}" class="class-card">
                                            <i class="fas fa-{{ item.icon }} class-icon"></i>
                                            <span>{{ item.classe.nom }}</span>
                                        </a>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endif %}

                        {% if categories.Lycée %}
                            <div class="category-section">
                                <h5 class="category-title">Lycée</h5>
                                <div class="class-grid">
                                    {% for item in categories.Lycée %}
                                        <a href="{% url 'class_detail' item.classe.id %}" class="class-card">
                                            <i class="fas fa-{{ item.icon }} class-icon"></i>
                                            <span>{{ item.classe.nom }}</span>
                                        </a>
                                    {% endfor %}
                                </div>
                            </div>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<!-- Styling -->
<style>
    /* Main layout grid */
    .main-layout {
        display: grid;
        grid-template-columns: 1fr 2fr 1fr;
        gap: 20px;
    }

    /* Panel styling */
    .panel {
        background: #fff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .panel-title {
        font-size: 1.2rem;
        margin-bottom: 15px;
        font-weight: bold;
        text-align: center;
    }

    /* Quick Access Grid */
    .quick-access-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
    }
    .quick-btn {
        font-size: 1rem;
        padding: 10px;
        text-align: center;
    }

    /* School Section Grid */
    .school-grid {
        display: grid;
        gap: 20px;
    }
    .school-section {
        margin-bottom: 20px;
    }

    /* Class Grid */
    .class-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
        gap: 10px;
    }
    .class-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: #007bff;
        color: #fff;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        transition: transform 0.2s;
        text-decoration: none;
    }
    .class-card:hover {
        transform: scale(1.05);
    }
    .class-icon {
        font-size: 1.5rem;
        margin-bottom: 5px;
    }
</style>
{% endblock %}