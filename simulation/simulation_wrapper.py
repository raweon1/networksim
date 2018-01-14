from math import sqrt
from scipy import stats


def simulate_multiple(simulation_generator_list, count, runtime, confidence_coefficient):
    results = {}
    for simulation_generator in simulation_generator_list:
        results.update(simulate_same_multiple(simulation_generator, count, runtime, confidence_coefficient))
    return results


def simulate_same_multiple(simulation_generator, count, runtime, confidence_coefficient, return_singles=False):
    simulation_results = []
    name = "empty"
    for i in range(0, count):
            sim_env = simulation_generator.__next__()
            name = sim_env.name
            sim_env.run(runtime)
            simulation_results.append(sim_env.get_monitor_results())
    result = get_confidence_interval(simulation_results, confidence_coefficient)
    if not return_singles:
        return {name: result}
    return {name: {"combined_result": result, "single_results": simulation_results}}


def default_callback(sim_env):
    print(sim_env.now)
    print(sim_env.get_monitor_results())


def simulate_in_steps(simulation_generator, step_count, runtime, callback=default_callback):
    sim_env = simulation_generator.__next__()
    for i in range(1, step_count + 1):
        sim_env.run(runtime * i)
        callback(sim_env)
    return sim_env.get_monitor_results()


def get_confidence_interval(list_of_dicts, confidence_coefficient):
    result = {}
    for key, value in list_of_dicts[0].items():
        if isinstance(value, dict):
            result[key] = get_confidence_interval([_dict[key] for _dict in list_of_dicts], confidence_coefficient)
        else:
            list_of_values = [_dict[key] for _dict in list_of_dicts]
            _average = average(list_of_values)
            _standard_deviation = standard_deviation(list_of_values, _average)
            quantile = stud_t(confidence_coefficient, list_of_values.__len__() - 1)
            some = quantile * _standard_deviation / sqrt(list_of_values.__len__())
            lower = _average - some
            upper = _average + some
            result[key] = {"average": _average,
                           "standard_deviation": _standard_deviation,
                           "lower": lower,
                           "upper": upper}
    return result


def average(list_of_values):
    result = 0
    for value in list_of_values:
        result += value / list_of_values.__len__()
    return result


def standard_deviation(list_of_values, mean):
    result = 0
    for value in list_of_values:
        result += pow(value - mean, 2) / (list_of_values.__len__() - 1)
    return sqrt(result)


def stud_t(confidence_coefficient, degree_of_freedom):
    return stats.t.ppf(1 - ((1 - confidence_coefficient) / 2), degree_of_freedom)
