def remove_outdated_slot(container, curr_slot_number, nr_slot):
    slot_to_delete = curr_slot_number - nr_slot
    if slot_to_delete in container:
        del(container[slot_to_delete])

    if len(container) < nr_slot * 2:
        return

    keys = container.keys()

    for slot_number in keys:
        if slot_number < curr_slot_number - nr_slot:
            del(container[slot_number])
