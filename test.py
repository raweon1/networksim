from scipy import stats
from math import sqrt


def foo(a, b):
    if isinstance(b, dict):
        for key, value in b.items():
            foo(key, value)
    else:
        print(b)


tmp = [{'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 6989.699254444522, 'standard_deviation_latency': 3847.7589602017847},
        'Switch': {1: {'average_waiting_time': {-1: 6360.518481173122, 1: 6360.518481173122},
                       'standard_deviation_waiting_time': {-1: 14810297.513251778, 1: 14810297.513251778},
                       'average_queue_length': 10.204262736706356, 'standard_deviation_queue_length': 6.358319360505525,
                       'average_packet_size': 776.0000000000001,
                       'standard_deviation_packet_size': 1.1368683772161633e-13}}, 'Switch-2': {
        1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
            'average_queue_length': 0.00012897524838271642, 'standard_deviation_queue_length': 0.01135526227344746,
            'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
        2: {'average_waiting_time': {-1: 620.7999999999936, 1: 620.7999999999936},
            'standard_deviation_waiting_time': {-1: 4.672705340072264e-23, 1: 4.672705340072264e-23},
            'average_queue_length': 1.9177937492138073, 'standard_deviation_queue_length': 0.2737861216144041,
            'average_packet_size': 776.0000000000088, 'standard_deviation_packet_size': 8.753886504564481e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 5046.398237975325, 'standard_deviation_latency': 2800.63747306427},
        'Switch': {1: {'average_waiting_time': {-1: 4438.76968315785, 1: 4438.76968315785},
                       'standard_deviation_waiting_time': {-1: 7910329.741932017, 1: 7910329.741932017},
                       'average_queue_length': 7.710513120897394, 'standard_deviation_queue_length': 4.957909187165739,
                       'average_packet_size': 776.0000000000027,
                       'standard_deviation_packet_size': 2.7284841053187823e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00013635465042396533, 'standard_deviation_queue_length': 0.011675507174327249,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999942, 1: 620.7999999999942},
               'standard_deviation_waiting_time': {-1: 4.6825260078096e-23, 1: 4.6825260078096e-23},
               'average_queue_length': 1.944671481578093, 'standard_deviation_queue_length': 0.22259892132927447,
               'average_packet_size': 776.0000000000033, 'standard_deviation_packet_size': 3.2969182939268645e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 10383.814767650716, 'standard_deviation_latency': 4322.74199129742},
        'Switch': {1: {'average_waiting_time': {-1: 9763.236728091935, 1: 9763.236728091935},
                       'standard_deviation_waiting_time': {-1: 18647354.181637388, 1: 18647354.181637388},
                       'average_queue_length': 15.951646430246509, 'standard_deviation_queue_length': 7.141224204249206,
                       'average_packet_size': 776.0000000000032,
                       'standard_deviation_packet_size': 3.1832314562052626e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00013523038309910834, 'standard_deviation_queue_length': 0.011627287347402865,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999939, 1: 620.7999999999939},
               'standard_deviation_waiting_time': {-1: 4.580945256612901e-23, 1: 4.580945256612901e-23},
               'average_queue_length': 1.95389573134858, 'standard_deviation_queue_length': 0.20690314835580745,
               'average_packet_size': 776.0000000000092, 'standard_deviation_packet_size': 9.208633855450847e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 9415.298581547057, 'standard_deviation_latency': 3573.8379805245418},
        'Switch': {1: {'average_waiting_time': {-1: 8792.647829900277, 1: 8792.647829900277},
                       'standard_deviation_waiting_time': {-1: 12747756.072440868, 1: 12747756.072440868},
                       'average_queue_length': 14.470848532571962, 'standard_deviation_queue_length': 5.825473129507963,
                       'average_packet_size': 776.0000000000041,
                       'standard_deviation_packet_size': 4.092726157978167e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.0001353451834976881, 'standard_deviation_queue_length': 0.011632220309966293,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999943, 1: 620.7999999999943},
               'standard_deviation_waiting_time': {-1: 4.820103549117996e-23, 1: 4.820103549117996e-23},
               'average_queue_length': 1.9684817442705134, 'standard_deviation_queue_length': 0.16922848417560907,
               'average_packet_size': 775.9999999999911, 'standard_deviation_packet_size': 8.867573342286037e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 9066.65851629672, 'standard_deviation_latency': 3677.3330379970002},
        'Switch': {1: {'average_waiting_time': {-1: 8455.932126895386, 1: 8455.932126895386},
                       'standard_deviation_waiting_time': {-1: 13542731.984475255, 1: 13542731.984475255},
                       'average_queue_length': 14.385812083158656, 'standard_deviation_queue_length': 5.949075224092742,
                       'average_packet_size': 775.9999999999997,
                       'standard_deviation_packet_size': 3.410605131648487e-13}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.000140176828320089, 'standard_deviation_queue_length': 0.01183796992681194,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999944, 1: 620.7999999999944},
               'standard_deviation_waiting_time': {-1: 4.8302851281846854e-23, 1: 4.8302851281846854e-23},
               'average_queue_length': 1.990933409383838, 'standard_deviation_queue_length': 0.08821001115211549,
               'average_packet_size': 776.0000000000042, 'standard_deviation_packet_size': 4.2064129956997834e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 4886.458261934422, 'standard_deviation_latency': 3122.6163490644676},
        'Switch': {1: {'average_waiting_time': {-1: 4258.353936760203, 1: 4258.353936760203},
                       'standard_deviation_waiting_time': {-1: 9757762.193417039, 1: 9757762.193417039},
                       'average_queue_length': 6.907295515579626, 'standard_deviation_queue_length': 5.111344525188625,
                       'average_packet_size': 775.9999999999957,
                       'standard_deviation_packet_size': 4.320099833421425e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00012760282063423026, 'standard_deviation_queue_length': 0.01129470042773393,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999936, 1: 620.7999999999936},
               'standard_deviation_waiting_time': {-1: 4.6905023331519406e-23, 1: 4.6905023331519406e-23},
               'average_queue_length': 1.8983657418155309, 'standard_deviation_queue_length': 0.30102538903926473,
               'average_packet_size': 776.0000000000085, 'standard_deviation_packet_size': 8.526512829121222e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 7954.567016997986, 'standard_deviation_latency': 6084.370332116776},
        'Switch': {1: {'average_waiting_time': {-1: 7344.628548273728, 1: 7344.628548273728},
                       'standard_deviation_waiting_time': {-1: 36998668.267385885, 1: 36998668.267385885},
                       'average_queue_length': 12.327608366343323, 'standard_deviation_queue_length': 9.973992156290382,
                       'average_packet_size': 776.0000000000033,
                       'standard_deviation_packet_size': 3.2969182939268645e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00013549730461112584, 'standard_deviation_queue_length': 0.011638753715912949,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.799999999994, 1: 620.799999999994},
               'standard_deviation_waiting_time': {-1: 4.716649179279715e-23, 1: 4.716649179279715e-23},
               'average_queue_length': 1.9369204245277414, 'standard_deviation_queue_length': 0.23835964192284884,
               'average_packet_size': 776.0000000000078, 'standard_deviation_packet_size': 7.844391802791501e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 6572.7295735427, 'standard_deviation_latency': 3416.3856523969876},
        'Switch': {1: {'average_waiting_time': {-1: 5942.82908222739, 1: 5942.82908222739},
                       'standard_deviation_waiting_time': {-1: 11689414.809794279, 1: 11689414.809794279},
                       'average_queue_length': 9.849893127020769, 'standard_deviation_queue_length': 5.563318575006471,
                       'average_packet_size': 776.0000000000085,
                       'standard_deviation_packet_size': 8.526512829121222e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.0001331884122301213, 'standard_deviation_queue_length': 0.011539191318565881,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.799999999994, 1: 620.799999999994},
               'standard_deviation_waiting_time': {-1: 4.781024884059324e-23, 1: 4.781024884059324e-23},
               'average_queue_length': 1.971898528541425, 'standard_deviation_queue_length': 0.16509960890559647,
               'average_packet_size': 776.0000000000001, 'standard_deviation_packet_size': 1.1368683772161633e-13}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 6569.654740006922, 'standard_deviation_latency': 4021.1196454340325},
        'Switch': {1: {'average_waiting_time': {-1: 5938.591718745272, 1: 5938.591718745272},
                       'standard_deviation_waiting_time': {-1: 16189112.676713767, 1: 16189112.676713767},
                       'average_queue_length': 9.424935146738253, 'standard_deviation_queue_length': 6.615793211125664,
                       'average_packet_size': 776.0000000000001,
                       'standard_deviation_packet_size': 1.1368683772161633e-13}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.0001274680458614842, 'standard_deviation_queue_length': 0.011288735612422085,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999942, 1: 620.7999999999942},
               'standard_deviation_waiting_time': {-1: 4.7764885729249665e-23, 1: 4.7764885729249665e-23},
               'average_queue_length': 1.8909181588492467, 'standard_deviation_queue_length': 0.30864120811233753,
               'average_packet_size': 776.0000000000088, 'standard_deviation_packet_size': 8.753886504564481e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 15743.060537746758, 'standard_deviation_latency': 8402.143772235344},
        'Switch': {1: {'average_waiting_time': {-1: 15128.929856786302, 1: 15128.929856786302},
                       'standard_deviation_waiting_time': {-1: 70468480.2023756, 1: 70468480.2023756},
                       'average_queue_length': 25.145721143677903,
                       'standard_deviation_queue_length': 13.531727482728623, 'average_packet_size': 776.0000000000039,
                       'standard_deviation_packet_size': 3.865352482534932e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00013803357928915552, 'standard_deviation_queue_length': 0.011747147542323783,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999942, 1: 620.7999999999942},
               'standard_deviation_waiting_time': {-1: 4.7494662453714714e-23, 1: 4.7494662453714714e-23},
               'average_queue_length': 1.9657911902045349, 'standard_deviation_queue_length': 0.18024480766500922,
               'average_packet_size': 776.0000000000078, 'standard_deviation_packet_size': 7.844391802791483e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 5011.339839763154, 'standard_deviation_latency': 4184.049327751494},
        'Switch': {1: {'average_waiting_time': {-1: 4415.601385818679, 1: 4415.601385818679},
                       'standard_deviation_waiting_time': {-1: 17765005.418280732, 1: 17765005.418280732},
                       'average_queue_length': 7.62510595699303, 'standard_deviation_queue_length': 7.715256814141902,
                       'average_packet_size': 776.0000000000051,
                       'standard_deviation_packet_size': 5.115907697472698e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00013134377281445416, 'standard_deviation_queue_length': 0.011459025818409515,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999942, 1: 620.7999999999942},
               'standard_deviation_waiting_time': {-1: 4.6485854573507763e-23, 1: 4.6485854573507763e-23},
               'average_queue_length': 1.846475429044307, 'standard_deviation_queue_length': 0.35996896111606813,
               'average_packet_size': 776.0000000000045, 'standard_deviation_packet_size': 4.547473508864634e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 11408.72809697413, 'standard_deviation_latency': 9571.209871486757},
        'Switch': {1: {'average_waiting_time': {-1: 10816.77363547555, 1: 10816.77363547555},
                       'standard_deviation_waiting_time': {-1: 91784479.5634617, 1: 91784479.5634617},
                       'average_queue_length': 19.068221298695196,
                       'standard_deviation_queue_length': 16.580322742189413, 'average_packet_size': 775.9999999999974,
                       'standard_deviation_packet_size': 2.614797267597179e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00014282485251384646, 'standard_deviation_queue_length': 0.011949228324470608,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999944, 1: 620.7999999999944},
               'standard_deviation_waiting_time': {-1: 4.729545217271033e-23, 1: 4.729545217271033e-23},
               'average_queue_length': 1.9242762294305913, 'standard_deviation_queue_length': 0.2621457073657156,
               'average_packet_size': 775.999999999996, 'standard_deviation_packet_size': 3.979039320256541e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 9871.215732356342, 'standard_deviation_latency': 6111.772751986092},
        'Switch': {1: {'average_waiting_time': {-1: 9259.828160500636, 1: 9259.828160500636},
                       'standard_deviation_waiting_time': {-1: 37318382.25763904, 1: 37318382.25763904},
                       'average_queue_length': 15.38800245399325, 'standard_deviation_queue_length': 10.103127991271473,
                       'average_packet_size': 776.0000000000027,
                       'standard_deviation_packet_size': 2.7284841053187823e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.0001350113976278329, 'standard_deviation_queue_length': 0.011617871747176944,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.799999999994, 1: 620.799999999994},
               'standard_deviation_waiting_time': {-1: 4.8072533819460285e-23, 1: 4.8072533819460285e-23},
               'average_queue_length': 1.9310945286132992, 'standard_deviation_queue_length': 0.24724392169013315,
               'average_packet_size': 776.0000000000033, 'standard_deviation_packet_size': 3.2969182939268645e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 4777.799716756877, 'standard_deviation_latency': 2538.014921468864},
        'Switch': {1: {'average_waiting_time': {-1: 4160.432842576711, 1: 4160.432842576711},
                       'standard_deviation_waiting_time': {-1: 6434137.309507791, 1: 6434137.309507791},
                       'average_queue_length': 6.839615119752782, 'standard_deviation_queue_length': 4.258040182501584,
                       'average_packet_size': 776.0000000000066,
                       'standard_deviation_packet_size': 6.593836587853753e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00012936102611091615, 'standard_deviation_queue_length': 0.011372227562158886,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999937, 1: 620.7999999999937},
               'standard_deviation_waiting_time': {-1: 4.552435125246188e-23, 1: 4.552435125246188e-23},
               'average_queue_length': 1.8873243078354667, 'standard_deviation_queue_length': 0.31448858548167113,
               'average_packet_size': 776.0000000000053, 'standard_deviation_packet_size': 5.343281372915958e-12}}},
       {'Injector': {'average_packet_size': 776.0000000000066, 'standard_deviation_packet_size': 6.593836587853749e-12,
                     'average_package_latency': 3522.1346022091207, 'standard_deviation_latency': 1992.7288771820272},
        'Switch': {1: {'average_waiting_time': {-1: 2902.8596248678946, 1: 2902.8596248678946},
                       'standard_deviation_waiting_time': {-1: 3964095.1125060506, 1: 3964095.1125060506},
                       'average_queue_length': 4.739965591115731, 'standard_deviation_queue_length': 3.28348155260604,
                       'average_packet_size': 775.9999999999927,
                       'standard_deviation_packet_size': 7.275957614183445e-12}}, 'Switch-2': {
           1: {'average_waiting_time': {-1: 20.8, 20: 20.8}, 'standard_deviation_waiting_time': {-1: 0.0, 20: 0.0},
               'average_queue_length': 0.00012459081152623036, 'standard_deviation_queue_length': 0.011160634736411896,
               'average_packet_size': 26.0, 'standard_deviation_packet_size': 0.0},
           2: {'average_waiting_time': {-1: 620.7999999999937, 1: 620.7999999999937},
               'standard_deviation_waiting_time': {-1: 4.475560962192198e-23, 1: 4.475560962192198e-23},
               'average_queue_length': 1.8553107216253961, 'standard_deviation_queue_length': 0.34804380618182995,
               'average_packet_size': 775.999999999997, 'standard_deviation_packet_size': 2.9558577807620067e-12}}}
       ]


def foo2(list_of_dicts, konfidenzniveau):
    result = {}
    for key, value in list_of_dicts[0].items():
        if isinstance(value, dict):
            result[key] = foo2([_dict[key] for _dict in list_of_dicts], konfidenzniveau)
        else:
            list_of_values = [_dict[key] for _dict in list_of_dicts]
            _average = average(list_of_values)
            _standard_deviation = standard_deviation(list_of_values, _average)
            quantile = stud_t(konfidenzniveau, list_of_values.__len__() - 1)
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
    count = list_of_values.__len__() - 1
    for value in list_of_values:
        result += pow(value - mean, 2) / count
    return sqrt(result)


def stud_t(konfidenzniveau, freiheitsgrad):
    return stats.t.ppf(1 - ((1 - konfidenzniveau) / 2), freiheitsgrad)


#print(foo2(tmp, 0.95))
