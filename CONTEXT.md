# Gradebook

A teacher-facing web app for recording student work and computing per-subject
grades. Modelled around a combination class: a single class holding students of
more than one grade level, teaching multiple subjects that are graded
independently.

## Language

### People & groups

**Teacher**:
The person who owns classes and records grades. The sole user of the app in v1.
_Avoid_: Instructor, user

**Student**:
A child enrolled in a Class. Belongs to exactly one Grade Level.
_Avoid_: Pupil, learner

**Class**:
A group of Students a Teacher teaches together. May span more than one Grade
Level (e.g. a combined 1st/2nd grade class).
_Avoid_: Section, course, room, homeroom

**Grade Level**:
The year cohort a Student belongs to — e.g. 1st grade, 2nd grade. Determines
which Assignments apply to the Student. Never shortened to "grade" (see Grade).
_Avoid_: Year, level, grade (the mark)

### Coursework & grading

**Subject**:
An area of study within a Class that is graded independently — e.g. Math,
Reading. Each Student has a separate Grade per Subject.
_Avoid_: Course, class (the group), topic

**Assignment**:
A gradeable piece of work within a Subject, worth some maximum number of points.
Applies to one or more Grade Levels (see Audience).
_Avoid_: Task, activity

**Audience**:
The set of Grade Levels an Assignment applies to — 1st only, 2nd only, or both.
A Student's Grade counts only the Assignments whose Audience includes their
Grade Level; an Assignment outside a Student's Audience is simply not counted for
them — it is not a zero.
_Avoid_: Target, eligibility, applies-to

**Score**:
The points a Student earned on a single Assignment. Distinct from a Grade, which
is the computed rollup.
_Avoid_: Mark, result, points

**Category**:
A weighted grouping of Assignments within a Subject — e.g. Homework, Tests. Each
Category carries a weight, and a Subject's Grade is the weighted roll-up of its
Categories. Weights are evaluated per Student over only the Assignments in that
Student's Audience.
_Avoid_: Bucket, group, assignment type

**Grade**:
The computed overall mark for one Student in one Subject, derived from their
Scores via the Subject's Category weights. Expressed as a percentage and the
Letter Grade derived from it. The word "grade" always means this — never the
Grade Level.
_Avoid_: Mark, result, final grade

**Letter Grade**:
The A–F band a percentage Grade falls into, per the Grading Scale.
_Avoid_: Mark

**Grading Scale**:
The set of cutoffs mapping a percentage Grade to a Letter Grade — e.g. 90–100 = A.
Owned by a Class; every Subject in the Class shares it.
_Avoid_: Rubric, curve, scheme
