from django import template

register = template.Library()

@register.filter
def filter_year(units, year):
    """Filter units by year of study"""
    return [unit for unit in units if unit.year_of_study == year]

@register.filter
def filter_year_semester(units, year_semester):
    """Filter units by year and semester (format: 'year-semester' or integer)"""
    if isinstance(year_semester, str):
        # If it's a string, split by hyphen
        try:
            year, semester = map(int, year_semester.split('-'))
        except ValueError:
            # Handle case where the string format is invalid
            return []
    elif isinstance(year_semester, int):
        # If it's a single integer, assume it's the year and show all semesters
        year = year_semester
        # Return all units for this year regardless of semester
        return [unit for unit in units if unit.year_of_study == year]
    else:
        # Handle unexpected type
        return []
    
    # Filter by both year and semester
    return [unit for unit in units if unit.year_of_study == year and unit.semester == semester]