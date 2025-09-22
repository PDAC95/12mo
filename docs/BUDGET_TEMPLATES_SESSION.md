# Budget Templates System - Design Session

## 📅 Session Date: September 22, 2025

## ✅ Decisions Made

### **Template Types Defined:**

#### Financial Frameworks (3):
- **50/30/20 Rule** - Most popular balanced approach
- **Zero-based Budget** - Every dollar assigned
- **60/20/20 Aggressive** - Higher savings focus

#### Practical Situations (5):
- **Casa** - Home/household budget
- **Roommates** - Shared living expenses
- **Viaje de Negocios** - Business travel planning
- **Plan Evento** - Event planning budget
- **Oficina/Negocio** - Business/office expenses

### **User Experience Design:**

#### Template Philosophy:
- Templates are **starting points**, not rigid rules
- Users get intelligent structure but full customization freedom
- Focus on education and guidance, not restriction

#### UI Flow Confirmed:
1. **Título del presupuesto** (Budget title input)
2. **Template selection** with explanations
3. **Customization screen** with visual sections
4. **Save personalized budget**

#### Visual Layout:
- **Horizontal stacked sections** (not columns or cards)
- Clear percentage and amount display per section
- Real-time visual feedback on changes

#### Framework Example (50/30/20):
```
🟢 NECESIDADES (50% - $1,825)
├─ Vivienda: $1,200
├─ Comida: $400
└─ Transporte: $225

🟡 GUSTOS (30% - $1,095)
├─ Entretenimiento: $300
├─ Compras: $400
└─ Restaurantes: $395

🔵 AHORROS (20% - $730)
├─ Emergencias: $365
└─ Inversiones: $365
```

#### User Feedback System:
- **First modification:** Alert message "Estás modificando los porcentajes del framework 50/30/20"
- **Subsequent changes:** Only visual percentage updates
- **Real-time tracking:** Show current vs original percentages

#### Template Explanations:
**50/30/20 Rule Example:**
"Asigna 50% a necesidades básicas, 30% a gustos personales y 20% a ahorros. Si no puedes ahorrar el 20%, empieza con menos pero mantén el orden de prioridades."

## 🤔 Pending Questions for Next Session

### **Technical Implementation:**

#### **Categories Approach:**
- **Option A:** Use existing 10 base categories for all templates
- **Option B:** Create specific categories per template (e.g., "Vuelos" for travel)
- **Question:** Which approach for category management?

#### **Data Structure:**
- How to store template definitions
- Relationship between templates and existing budget system
- Percentage vs fixed amount handling

#### **Customization System:**
- Real-time calculation engine
- Validation rules for modifications
- How to handle template "drift" over time

### **Extended Features:**
- Should templates learn from user behavior?
- Template sharing between users?
- Seasonal template variations?

### **Integration Points:**
- How templates connect with existing space system
- Member assignment in template categories
- Template copying between months

## 📋 Next Session Agenda

1. **Resolve categories approach** (base vs specific)
2. **Define data models** and relationships
3. **Plan implementation phases**
4. **Design template creation workflow**
5. **Specify testing requirements**

## 💾 Current System Context

**What we have:**
- Working budget system with 10 categories
- Monthly budget creation
- Space integration
- Member assignment
- Progress tracking

**What we're adding:**
- Template-based budget creation
- Framework education
- Visual percentage tracking
- Smart customization

---

**Next Session:** Continue with technical design and implementation planning
**Focus:** Categories approach and data structure decisions